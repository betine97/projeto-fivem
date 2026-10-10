using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.IO.Compression;
using SharpDX;
using CodeWalker.GameFiles;

public static class RelocarCayo
{
    static readonly Vector3 Delta = new Vector3(-1300, 5200, 0);
    static void Check(bool good, string message) { if (!good) throw new Exception(message); }
    static int Count<T>(T[] a) { return a == null ? 0 : a.Length; }
    static byte[] ShiftNativeBounds(byte[] packed, BoundComposite comp)
    {
        Check(BitConverter.ToUInt32(packed,0)==0x37435352,"Expected native RSC7 collision");
        byte[] raw;
        using(var input=new MemoryStream(packed,16,packed.Length-16))
        using(var zip=new DeflateStream(input,CompressionMode.Decompress))
        using(var outStream=new MemoryStream()){zip.CopyTo(outStream);raw=outStream.ToArray();}
        var patched=new HashSet<long>();
        Action<long> move=p=>{
            long n=p-0x50000000L;Check(n>=0 && n+12<=raw.Length,"Invalid system pointer "+p.ToString("X")+" raw="+raw.Length);
            if(!patched.Add(n))return;
            float[] delta={Delta.X,Delta.Y,Delta.Z};
            for(int i=0;i<3;i++){int k=(int)n+i*4;float v=BitConverter.ToSingle(raw,k)+delta[i];Array.Copy(BitConverter.GetBytes(v),0,raw,k,4);}
        };
        Action<long> header=p=>{move(p+0x20);move(p+0x30);move(p+0x40);move(p+0x50);};
        Action<long> bvh=p=>{if(p!=0){move(p+0x20);move(p+0x30);move(p+0x40);}};
        header(0x50000000L);bvh((long)comp.BVHPointer);
        for(int i=0;i<comp.Children.data_items.Length;i++)
        {
            var child=comp.Children.data_items[i];if(child==null)continue;
            Check(child.Transform==Matrix.Identity,"World collision has nonidentity local transform");
            var geom=child as BoundBVH;Check(geom!=null,"Unsupported world collision child");
            long childPointer=BitConverter.ToInt64(raw,checked((int)((long)comp.ChildrenPointer-0x50000000L+i*8)));
            header(childPointer);move(childPointer+0xA0);bvh((long)geom.BvhPointer);
            if(comp.ChildrenBoundingBoxesPointer!=0){move((long)comp.ChildrenBoundingBoxesPointer+i*32);move((long)comp.ChildrenBoundingBoxesPointer+i*32+16);}
        }
        // Preserve every vertex, primitive, material, transform, quantization value and BVH node byte.
        using(var result=new MemoryStream())
        {
            result.Write(packed,0,16);
            using(var zip=new DeflateStream(result,CompressionLevel.Optimal,true))zip.Write(raw,0,raw.Length);
            return result.ToArray();
        }
    }
    public static string[] Maps(string source, string output, string[] selected)
    {
        Directory.CreateDirectory(output);
        var maps = new Dictionary<uint,YmapFile>();
        var hashes = new Dictionary<uint,uint>();
        foreach(var name in selected)
        {
            var y = new YmapFile();
            y.Load(File.ReadAllBytes(Path.Combine(source,name))); y.Name = name;
            uint fileHash=JenkHash.GenHash(Path.GetFileNameWithoutExtension(name));
            maps[fileHash] = y;
            hashes[fileHash] = JenkHash.GenHash("cv_"+Path.GetFileNameWithoutExtension(name));
        }
        // Link lights before serializing: otherwise CodeWalker drops unlinked LOD arrays.
        foreach(var y in maps.Values)
        {
            YmapFile parent;
            if(maps.TryGetValue(y.CMapData.parent.Hash,out parent))
            {
                y.Parent=parent;
                if(y.LODLights!=null && parent.DistantLODLights!=null) y.LODLights.Init(parent.DistantLODLights);
            }
        }
        var report=new List<string>();
        foreach(var y in maps.Values)
        {
            string original=y.Name;
            int ents=Count(y.AllEntities), mlos=Count(y.MloEntities), grass=Count(y.GrassInstanceBatches);
            int lights=Count(y.LODLights==null?null:y.LODLights.direction);
            int distant=Count(y.DistantLODLights==null?null:y.DistantLODLights.positions);
            Check(y.CMapData.containerLods.Count1==0 && y.CMapData.instancedData.PropInstanceList.Count1==0,"Unsupported containers "+original);
            var oldPositions=y.AllEntities==null?new Vector3[0]:y.AllEntities.Select(e=>e.Position).ToArray();
            var oldMin=y.CMapData.entitiesExtentsMin;
            if(y.AllEntities!=null) foreach(var e in y.AllEntities) e.SetPosition(e.Position+Delta);
            if(y.CarGenerators!=null) foreach(var c in y.CarGenerators) c.SetPosition(c.Position+Delta);
            if(y.GrassInstanceBatches!=null) foreach(var b in y.GrassInstanceBatches)
            { b.Position+=Delta; b.AABBMin+=Delta; b.AABBMax+=Delta; }
            if(y.DistantLODLights!=null && y.DistantLODLights.positions!=null)
                for(int i=0;i<y.DistantLODLights.positions.Length;i++)
                    y.DistantLODLights.positions[i]=new MetaVECTOR3(y.DistantLODLights.positions[i].ToVector3()+Delta);
            if(y.CTimeCycleModifiers!=null) for(int i=0;i<y.CTimeCycleModifiers.Length;i++)
            { var v=y.CTimeCycleModifiers[i];v.minExtents+=Delta;v.maxExtents+=Delta;y.CTimeCycleModifiers[i]=v; }
            // Preserve the original occlusion box rotations; the editor's generic rebuild changes their magnitude.
            if(y.CBoxOccluders!=null) for(int i=0;i<y.CBoxOccluders.Length;i++)
            { var v=y.CBoxOccluders[i];v.iCenterX=checked((short)(v.iCenterX+Delta.X*4));v.iCenterY=checked((short)(v.iCenterY+Delta.Y*4));y.CBoxOccluders[i]=v; }
            y.BoxOccluders=null;
            if(y.OccludeModels!=null) foreach(var model in y.OccludeModels)
                if(model.Triangles!=null) foreach(var t in model.Triangles) {t.Corner1+=Delta;t.Corner2+=Delta;t.Corner3+=Delta;}
            if(ents>0 || grass>0 || lights>0 || distant>0 || y.CMapData.occludeModels.Count1>0 || y.CMapData.boxOccluders.Count1>0)
            { y._CMapData.streamingExtentsMin+=Delta;y._CMapData.streamingExtentsMax+=Delta;y._CMapData.entitiesExtentsMin+=Delta;y._CMapData.entitiesExtentsMax+=Delta; }
            uint parentHash;
            y._CMapData.parent = new MetaHash(hashes.TryGetValue(y.CMapData.parent.Hash,out parentHash)?parentHash:0);
            y._CMapData.flags &= ~1u; // Selected normal exploration state, streamed alongside the authored island.
            y.Name="cv_"+original;
            var data=y.Save();
            Check(y.SaveWarnings==null || y.SaveWarnings.Count==0,"Save warnings "+original+": "+string.Join(";",y.SaveWarnings??new List<string>()));
            var re=new YmapFile();re.Load(data);
            Check(Count(re.AllEntities)==ents && Count(re.MloEntities)==mlos && Count(re.GrassInstanceBatches)==grass,"Lost map data "+original);
            Check(Count(re.LODLights==null?null:re.LODLights.direction)==lights && Count(re.DistantLODLights==null?null:re.DistantLODLights.positions)==distant,"Lost lights "+original);
            for(int i=0;i<ents;i++) Check(Vector3.Distance(re.AllEntities[i].Position,oldPositions[i]+Delta)<0.003f,"Entity misaligned "+original);
            File.WriteAllBytes(Path.Combine(output,y.Name),data);
            report.Add(original+"\t"+ents+"\t"+mlos+"\t"+grass+"\t"+lights+"\t"+distant);
        }
        return report.ToArray();
    }
    public static string[] BoundsFiles(string source,string output)
    {
        var report=new List<string>();
        foreach(var file in Directory.GetFiles(source,"*.ybn"))
        {
            var y=new YbnFile();y.Load(File.ReadAllBytes(file));var b=y.Bounds;
            bool world=b.BoxMin.X>3000 && b.BoxMax.Y< -3000;
            var oldMin=b.BoxMin;var oldMax=b.BoxMax;
            if(world)
            {
                var comp=b as BoundComposite;
                Check(comp!=null,"World collision is not composite "+file);
                var data=ShiftNativeBounds(File.ReadAllBytes(file),comp);var re=new YbnFile();re.Load(data);
                Check(Vector3.Distance(re.Bounds.BoxMin,oldMin+Delta)<0.003f && Vector3.Distance(re.Bounds.BoxMax,oldMax+Delta)<0.003f,"Collision bounds misaligned "+file);
                var cc=(BoundComposite)re.Bounds;
                Check(cc.Children.data_items.Length==comp.Children.data_items.Length,"Lost collision children "+file);
                for(int i=0;i<cc.Children.data_items.Length;i++)
                {
                    var a=comp.Children.data_items[i];var c=cc.Children.data_items[i];
                    if(a==null){Check(c==null,"Changed null child");continue;}
                    Check(Vector3.Distance(c.BoxMin,a.BoxMin+Delta)<0.003f && c.Transform==a.Transform,"Changed collision transform "+file);
                    var g=a as BoundGeometry;var h=c as BoundGeometry;
                    if(g!=null) Check(h!=null && Count(g.Vertices)==Count(h.Vertices) && Count(g.Polygons)==Count(h.Polygons),"Lost geometry "+file);
                }
                File.WriteAllBytes(Path.Combine(output,Path.GetFileName(file)),data);
            }
            else File.Copy(file,Path.Combine(output,Path.GetFileName(file)),true);
            report.Add(Path.GetFileName(file)+"\t"+(world?"world":"local"));
        }
        return report.ToArray();
    }
    public static string[] ProbeGround(string source,string output)
    {
        var points=new[]{new Vector3(4440,-4530,1000),new Vector3(4440,-4490,1000),new Vector3(4897,-5180,1000),new Vector3(5010,-5750,1000)};
        var before=Enumerable.Repeat(float.NegativeInfinity,points.Length).ToArray();
        var after=Enumerable.Repeat(float.NegativeInfinity,points.Length).ToArray();
        foreach(var file in Directory.GetFiles(source,"*.ybn"))
        {
            var a=new YbnFile();a.Load(File.ReadAllBytes(file));var b=a.Bounds;
            if(!(b.BoxMin.X>3000 && b.BoxMax.Y< -3000))continue;
            for(int i=0;i<points.Length;i++)
            {
                var p=points[i];if(p.X<b.BoxMin.X || p.X>b.BoxMax.X || p.Y<b.BoxMin.Y || p.Y>b.BoxMax.Y)continue;
                var oldRay=new Ray(p,-Vector3.UnitZ);var oldHit=b.RayIntersect(ref oldRay,1500);
                if(!oldHit.Hit)continue;
                var moved=new YbnFile();moved.Load(File.ReadAllBytes(Path.Combine(output,Path.GetFileName(file))));
                var newRay=new Ray(p+Delta,-Vector3.UnitZ);var newHit=moved.Bounds.RayIntersect(ref newRay,1500);
                Check(newHit.Hit && Math.Abs(oldHit.HitDist-newHit.HitDist)<0.01f,"Collision ray mismatch "+file+" point="+i+" old="+oldHit.Hit+","+oldHit.HitDist+" new="+newHit.Hit+","+newHit.HitDist);
                before[i]=Math.Max(before[i],p.Z-oldHit.HitDist);after[i]=Math.Max(after[i],p.Z-newHit.HitDist);
            }
        }
        var lines=new List<string>();
        for(int i=0;i<points.Length;i++)
        {Check(!float.IsInfinity(before[i]) && Math.Abs(before[i]-after[i])<0.01f,"Ground unavailable at probe");lines.Add((points[i].X+Delta.X)+"\t"+(points[i].Y+Delta.Y)+"\t"+after[i]);}
        return lines.ToArray();
    }
}
