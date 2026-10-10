using System;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Drawing.Imaging;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Windows.Forms;

static class Program {
    [DllImport("user32.dll")] static extern bool SetProcessDPIAware();
    [STAThread] static void Main(string[] args) {
        SetProcessDPIAware(); Application.EnableVisualStyles();
        if(args.Length > 0 && args[0] == "--self-test") { SelfTest(); return; }
        bool fresh; using(var mutex = new System.Threading.Mutex(true,"Local\\PrintRapidoApp",out fresh)) {
            if(!fresh) { MessageBox.Show("O Print Rápido já está aberto perto do relógio."); return; }
            Application.Run(new TrayApp());
        }
    }
    static void SelfTest() {
        using(var b = new Bitmap(100,80)) using(var g = Graphics.FromImage(b)) {
            g.Clear(Color.White); g.DrawLine(Pens.Red,10,10,60,60);
            using(var c = b.Clone(new Rectangle(5,5,70,65),PixelFormat.Format32bppArgb)) {
                if(c.Width!=70 || c.Height!=65 || c.GetPixel(5,5).G!=0 || c.GetPixel(0,0).G!=255) throw new Exception("Falha no recorte/desenho");
            }
        }
        var bounds=SystemInformation.VirtualScreen;
        using(var screen=new Bitmap(bounds.Width,bounds.Height)) using(var g=Graphics.FromImage(screen)) { g.CopyFromScreen(bounds.Location,Point.Empty,bounds.Size); }
        using(var f = new Capture(new Bitmap(120,100),new Rectangle(0,0,120,100))) { f.CreateControl(); }
        System.IO.File.WriteAllText(System.IO.Path.Combine(AppDomain.CurrentDomain.BaseDirectory,"teste-ok.txt"),"Recorte, desenho e criação da janela: OK");
    }
}

class TrayApp : ApplicationContext {
    delegate IntPtr HookProc(int code, IntPtr wp, IntPtr lp);
    [DllImport("user32.dll")] static extern IntPtr SetWindowsHookEx(int id, HookProc proc, IntPtr module, uint thread);
    [DllImport("user32.dll")] static extern bool UnhookWindowsHookEx(IntPtr hook);
    [DllImport("user32.dll")] static extern IntPtr CallNextHookEx(IntPtr hook,int code,IntPtr wp,IntPtr lp);
    [DllImport("kernel32.dll",CharSet=CharSet.Auto)] static extern IntPtr GetModuleHandle(string name);
    NotifyIcon tray; HookProc callback; IntPtr hook; bool down; Capture current;
    Control dispatcher = new Control();
    public TrayApp() {
        dispatcher.CreateControl();
        var menu = new ContextMenuStrip();
        menu.Items.Add("Capturar tela",null,delegate { Open(); });
        menu.Items.Add("Sair",null,delegate { ExitThread(); });
        tray = new NotifyIcon { Icon=SystemIcons.Application, Text="Print Rápido — tecla abaixo do Esc", ContextMenuStrip=menu, Visible=true };
        tray.DoubleClick += delegate { Open(); };
        callback = Keyboard; hook = SetWindowsHookEx(13,callback,GetModuleHandle(null),0);
        if(hook==IntPtr.Zero) MessageBox.Show("Não foi possível ativar a tecla. Use o ícone perto do relógio para capturar.");
        tray.ShowBalloonTip(4000,"Print Rápido","Pressione a tecla de aspas abaixo do Esc. Arraste para selecionar e use a caneta vermelha.",ToolTipIcon.Info);
    }
    IntPtr Keyboard(int code,IntPtr wp,IntPtr lp) {
        if(code>=0 && Marshal.ReadInt32(lp,4)==0x29 && (Control.ModifierKeys & (Keys.Control|Keys.Alt|Keys.Shift))==Keys.None) {
            int msg=wp.ToInt32();
            if(msg==0x100 || msg==0x104) { if(!down) { down=true; dispatcher.BeginInvoke((Action)Open); } return (IntPtr)1; }
            if(msg==0x101 || msg==0x105) { down=false; return (IntPtr)1; }
        }
        return CallNextHookEx(hook,code,wp,lp);
    }
    void Open() {
        if(current!=null) return;
        try {
            var bounds=SystemInformation.VirtualScreen;
            var bitmap=new Bitmap(bounds.Width,bounds.Height);
            try { using(var g=Graphics.FromImage(bitmap)) g.CopyFromScreen(bounds.Location,Point.Empty,bounds.Size); }
            catch { bitmap.Dispose(); throw; }
            current=new Capture(bitmap,bounds); current.FormClosed+=delegate { current=null; }; current.Show(); current.Activate();
        } catch(Exception e) { MessageBox.Show("Não foi possível capturar: "+e.Message); }
    }
    protected override void ExitThreadCore() { if(current!=null) current.Close(); if(hook!=IntPtr.Zero) UnhookWindowsHookEx(hook); tray.Dispose(); dispatcher.Dispose(); base.ExitThreadCore(); }
}

class Capture : Form {
    Bitmap shot; Rectangle area; Point start; Rectangle original; bool dragging, pen; int mode;
    List<List<Point>> strokes=new List<List<Point>>(); List<Point> stroke;
    FlowLayoutPanel bar=new FlowLayoutPanel(); Label help=new Label(); Button penButton;
    public Capture(Bitmap bitmap,Rectangle bounds) {
        shot=bitmap; FormBorderStyle=FormBorderStyle.None; StartPosition=FormStartPosition.Manual; Bounds=bounds;
        TopMost=true; DoubleBuffered=true; KeyPreview=true; Cursor=Cursors.Cross;
        bar.BackColor=Color.FromArgb(32,34,40); bar.Padding=new Padding(7); bar.AutoSize=true; bar.WrapContents=false;
        Add("Tela inteira",delegate { area=new Rectangle(Point.Empty,ClientSize); pen=false; RefreshUI(); });
        Add("Selecionar / ajustar",delegate { pen=false; RefreshUI(); });
        penButton=Add("Caneta vermelha",delegate { if(area.Width>0) { pen=!pen; RefreshUI(); } });
        Add("Desfazer",delegate { if(strokes.Count>0) strokes.RemoveAt(strokes.Count-1); Invalidate(); });
        Add("Copiar",delegate { Export(false); }); Add("Salvar PNG",delegate { Export(true); }); Add("Fechar (Esc)",delegate { Close(); });
        Controls.Add(bar); help.ForeColor=Color.White; help.BackColor=bar.BackColor; help.AutoSize=true; Controls.Add(help);
        RefreshUI();
        KeyDown+=delegate(object sender,KeyEventArgs e) { if(e.KeyCode==Keys.Escape) Close(); if(e.Control&&e.KeyCode==Keys.Z) { if(strokes.Count>0) strokes.RemoveAt(strokes.Count-1); Invalidate(); } if(e.Control&&e.KeyCode==Keys.C) Export(false); if(e.Control&&e.KeyCode==Keys.S) Export(true); };
    }
    Button Add(string text,Action action) { var b=new Button { Text=text,AutoSize=true,Height=32,BackColor=Color.White,FlatStyle=FlatStyle.Flat }; b.Click+=delegate { action(); }; bar.Controls.Add(b); return b; }
    void RefreshUI() {
        bar.Location=new Point(Math.Max(0,(ClientSize.Width-bar.PreferredSize.Width)/2),16);
        help.Text=pen ? "CANETA VERMELHA • arraste para desenhar • Ctrl+Z desfaz" : "Arraste para selecionar • arraste dentro para mover • arraste os cantos para redimensionar";
        help.Location=new Point(bar.Left,bar.Bottom+8); penButton.BackColor=pen?Color.LightCoral:Color.White; Invalidate();
    }
    protected override void OnPaint(PaintEventArgs e) {
        base.OnPaint(e); var g=e.Graphics; g.DrawImageUnscaled(shot,0,0);
        using(var shade=new SolidBrush(Color.FromArgb(125,0,0,0))) {
            var region=new Region(ClientRectangle); if(area.Width>0) region.Exclude(area); g.FillRegion(shade,region); region.Dispose();
        }
        if(area.Width>0) { using(var border=new Pen(Color.DeepSkyBlue,2)) g.DrawRectangle(border,area);
            foreach(var p in Corners()) g.FillRectangle(Brushes.White,p.X-5,p.Y-5,10,10);
            var state=g.Save(); g.SetClip(area); PaintStrokes(g); g.Restore(state);
        }
    }
    Point[] Corners() { return new[]{new Point(area.Left,area.Top),new Point(area.Right,area.Top),new Point(area.Right,area.Bottom),new Point(area.Left,area.Bottom)}; }
    void PaintStrokes(Graphics g) { g.SmoothingMode=SmoothingMode.AntiAlias; using(var p=new Pen(Color.Red,3)) { p.StartCap=LineCap.Round; p.EndCap=LineCap.Round; p.LineJoin=LineJoin.Round; foreach(var s in strokes) { if(s.Count>1) g.DrawLines(p,s.ToArray()); else if(s.Count==1) g.FillEllipse(Brushes.Red,s[0].X-1.5f,s[0].Y-1.5f,3,3); } } }
    protected override void OnMouseDown(MouseEventArgs e) {
        base.OnMouseDown(e); if(e.Button!=MouseButtons.Left) return; start=e.Location; original=area; dragging=true; Capture=true;
        if(pen) { if(!area.Contains(e.Location)) { dragging=false; Capture=false; return; } stroke=new List<Point>(); stroke.Add(e.Location); strokes.Add(stroke); mode=10; }
        else { mode=0; var corners=Corners(); if(area.Width>0) for(int i=0;i<4;i++) if(Math.Abs(e.X-corners[i].X)<=12&&Math.Abs(e.Y-corners[i].Y)<=12) mode=i+2;
            if(mode==0&&area.Contains(e.Location)) mode=1; if(mode==0) area=Rectangle.Empty; }
        Invalidate();
    }
    protected override void OnMouseMove(MouseEventArgs e) {
        base.OnMouseMove(e); if(!dragging) return;
        var p=new Point(Math.Max(0,Math.Min(ClientSize.Width-1,e.X)),Math.Max(0,Math.Min(ClientSize.Height-1,e.Y)));
        if(mode==10) { stroke.Add(p); }
        else if(mode==1) area=new Rectangle(Math.Max(0,Math.Min(ClientSize.Width-original.Width,original.X+p.X-start.X)),Math.Max(0,Math.Min(ClientSize.Height-original.Height,original.Y+p.Y-start.Y)),original.Width,original.Height);
        else { Point anchor=start; if(mode>=2) anchor=new[]{new Point(original.Right,original.Bottom),new Point(original.Left,original.Bottom),new Point(original.Left,original.Top),new Point(original.Right,original.Top)}[mode-2]; area=Rectangle.FromLTRB(Math.Min(anchor.X,p.X),Math.Min(anchor.Y,p.Y),Math.Max(anchor.X,p.X),Math.Max(anchor.Y,p.Y)); }
        Invalidate();
    }
    protected override void OnMouseUp(MouseEventArgs e) { base.OnMouseUp(e); dragging=false; Capture=false; if(area.Width<2||area.Height<2) area=Rectangle.Empty; Invalidate(); }
    void Export(bool save) {
        if(area.Width<2) { MessageBox.Show("Selecione uma área ou clique em Tela inteira."); return; }
        try { using(var result=shot.Clone(area,PixelFormat.Format32bppArgb)) {
            using(var g=Graphics.FromImage(result)) { g.TranslateTransform(-area.X,-area.Y); PaintStrokes(g); }
            if(save) { using(var dialog=new SaveFileDialog { Filter="Imagem PNG|*.png",FileName="Print-"+DateTime.Now.ToString("yyyy-MM-dd-HHmmss")+".png",InitialDirectory=Environment.GetFolderPath(Environment.SpecialFolder.MyPictures) }) { if(dialog.ShowDialog(this)!=DialogResult.OK) return; result.Save(dialog.FileName,ImageFormat.Png); } }
            else Clipboard.SetImage(result);
        } Close(); } catch(Exception ex) { MessageBox.Show("Não foi possível exportar: "+ex.Message); }
    }
    protected override void Dispose(bool disposing) { if(disposing && shot!=null) { shot.Dispose(); shot=null; } base.Dispose(disposing); }
}
