const fs=require('fs'),path=require('path'),http=require('http'),{spawn}=require('child_process');
const root=path.resolve(__dirname,'../../..'),ui=path.join(root,'server-data/resources/cidade_admin/ui');
const port=Number(fs.readFileSync(path.join(root,'painel_adm_20261009/preview-port.txt'),'utf8').trim());
const server=http.createServer((req,res)=>{
 const url=new URL(req.url,'http://localhost'),file=path.resolve(ui,'.'+(url.pathname==='/'?'/index.html':decodeURIComponent(url.pathname)));
 if(!file.startsWith(ui+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404);res.end();return}
 res.setHeader('Content-Type',({'.html':'text/html','.css':'text/css','.js':'application/javascript','.json':'application/json','.png':'image/png','.jpg':'image/jpeg','.svg':'image/svg+xml'})[path.extname(file)]||'application/octet-stream');res.end(fs.readFileSync(file));
});
server.listen(port,'127.0.0.1',()=>{
 const child=spawn(process.execPath,[path.join(root,'painel_adm_20261009/test_ui.cjs')],{cwd:root,stdio:'inherit',windowsHide:true});
 child.on('exit',code=>server.close(()=>process.exit(code||0)));
 child.on('error',error=>{console.error(error);server.close(()=>process.exit(1))});
});
server.on('error',error=>{console.error(error);process.exit(1)});
