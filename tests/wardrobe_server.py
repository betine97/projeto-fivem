"""Exercise the game-to-acervo bridge without changing real favorites or tags."""
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'personagens/calca_tatica/test_deps'))
from lupa import LuaRuntime
lua = LuaRuntime(unpack_returned_tuples=True)
files = {
    'catalog.json': {'items': [
        {'id':'favorite','category':'jbib','sex':'male'},
        {'id':'hidden','category':'jbib','sex':'female'},
        {'id':'shoeM','category':'feet','sex':'male'},
        {'id':'shoeF','category':'feet','sex':'female'},
    ]},
    'favorites.json': {'ids':['favorite','favorite','unknown']},
    'tags.json': {'items':{'shoeF':['OK']}},
    'hair.json': {'items':[]}, 'tattoos.json': {'items':[]},
    'exclusives.json': {'items':[]},
}
def convert(value):
    if not hasattr(value, 'items'): return value
    pairs = list(value.items())
    if pairs and all(isinstance(key,int) for key,_ in pairs):
        return [convert(value[index]) for index in range(1,len(pairs)+1)]
    return {key:convert(item) for key,item in pairs}
lua.globals().decode = lambda value: lua.table_from(json.loads(value), recursive=True)
lua.globals().encode = lambda value: json.dumps(convert(value))
lua.globals().load_file = lambda name: json.dumps(files[name])
lua.execute('''
events={};sent={};httpRequests={};source=1;clock=1000
json={decode=decode,encode=encode}
function GetCurrentResourceName()return 'cidade_acervo' end
function GetGameTimer()return clock end
function LoadResourceFile(_,name)return load_file(name) end
function RegisterNetEvent(name,callback)events[name]=callback end
function AddEventHandler(name,callback)events[name]=callback end
function CreateThread(callback)watcher=coroutine.create(callback) end
function Wait()coroutine.yield() end
function TriggerClientEvent(...)sent[#sent+1]={...} end
function PerformHttpRequest(url,callback,method,body,headers)
    httpRequests[#httpRequests+1]={url=url,callback=callback,method=method,body=body,headers=headers}
end
''')
lua.execute((ROOT/'server-data/resources/cidade_acervo/server.lua').read_text(encoding='utf-8'))
lua.execute('''
events['cidade_acervo:request'](10)
local result=sent[#sent]
assert(result[1]=='cidade_acervo:items' and result[2]==1 and result[3]==10)
assert(#result[4]==1 and result[5].total==1 and result[5].male==0 and result[5].female==1)
assert(result[4][1].id=='shoeF')
assert(result[7].shoeF[1]=='OK')
events['cidade_acervo:tags'](10,1,'shoeM',{'PEÇA INCORRETA'})
local request=httpRequests[1]
assert(request.method=='POST' and request.url=='http://127.0.0.1:8766/api/tags')
local body=json.decode(request.body)
assert(body.id=='shoeM' and body.tags[1]=='PEÇA INCORRETA')
events['cidade_acervo:tags'](10,2,'shoeF',{'OK'}) -- Reject another pending write.
assert(#httpRequests==1 and not sent[#sent][6].ok)
request.callback(200,json.encode({ok=true,id='shoeM',tags={'PEÇA INCORRETA'}}))
assert(sent[#sent][1]=='cidade_acervo:tagsSaved' and sent[#sent][6].ok)
events['cidade_acervo:tags'](10,3,'shoeM',{})
assert(httpRequests[2].body:find('"tags":%[%]'))
httpRequests[2].callback(500,'')
assert(not sent[#sent][6].ok)
events['cidade_acervo:tags'](10,4,'unknown',{'OK'})
events['cidade_acervo:tags'](10,5,'favorite',{'INVALID'})
assert(#httpRequests==2 and not sent[#sent][6].ok)
''')
files['tags.json']['items']['hidden']=['OK']
files['tags.json']['items']['favorite']=['DEFEITO NA TEXTURA']
lua.execute('''
assert(coroutine.resume(watcher)) -- Yield before the first poll.
assert(coroutine.resume(watcher)) -- Browser change is pushed to the open tablet.
local result=sent[#sent]
assert(result[1]=='cidade_acervo:items' and #result[4]==2 and result[5].female==2)
assert(result[4][1].id=='hidden' and result[6]==nil and result[7].hidden[1]=='OK')
local count=#sent
assert(coroutine.resume(watcher))
assert(#sent==count) -- Unchanged tags do not rebuild the preview.
events['cidade_acervo:closed'](9) -- Ignore an obsolete session closing.
''')
files['tags.json']['items'].pop('shoeF')
lua.execute('''
assert(coroutine.resume(watcher))
assert(#sent[#sent][4]==1 and sent[#sent][4][1].id=='hidden')
events['cidade_acervo:closed'](10)
''')
files['tags.json']['items']['favorite']=['OK']
lua.execute('''
local count=#sent
assert(coroutine.resume(watcher))
assert(#sent==count) -- Closed tablets are unsubscribed.
''')
assert files['favorites.json']=={'ids':['favorite','favorite','unknown']}
files['exclusives.json']=json.loads((ROOT/'server-data/resources/cidade_acervo/exclusives.json').read_text(encoding='utf-8'))
lua.globals().exclusiveCount=len(files['exclusives.json']['items'])
files['tags.json']={'items':{'shoeF':['OK']}}
lua.execute((ROOT/'server-data/resources/cidade_acervo/server.lua').read_text(encoding='utf-8'))
lua.execute('''
events['cidade_acervo:request'](20)
local result=sent[#sent]
assert(#result[4]==exclusiveCount+1 and result[5].exclusive==exclusiveCount and result[5].male==exclusiveCount and result[5].female==1)
local found={};for _,item in ipairs(result[4]) do found[item.id]=item end
assert(found['exclusive-west_texas'].collection=='cidade_west_texas_r002')
assert(found['exclusive-jeans_washed'].category=='lowr')
assert(not found.favorite and not result[7]['exclusive-west_texas'])
events['cidade_acervo:tags'](20,6,'exclusive-west_texas',{'PEÇA INCORRETA'})
assert(json.decode(httpRequests[#httpRequests].body).id=='exclusive-west_texas')
''')
print('PASS: only OK items, counts, live browser updates/removal, no repeated sends, closed sessions, serialized tag saves and favorites preserved')
