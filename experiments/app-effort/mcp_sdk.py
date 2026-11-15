"""Matched generic legacy read-only MCP helper; application supplies a zero-arg callback."""
import json,sys

def serve(server,version,tool,description,callback):
 def pairs(items):
  out={}
  for key,value in items:
   if key in out:raise ValueError('duplicate key')
   out[key]=value
  return out
 def reject_constant(value):raise ValueError('non-JSON constant')
 def reply(id,result=None,error=None):
  out=dict(jsonrpc='2.0',id=id);out['error'if error is not None else'result']=error if error is not None else result
  print(json.dumps(out,ensure_ascii=True,separators=(',',':')),flush=True)
 def error(id,code,message):reply(id,error=dict(code=-code,message=message))
 initialized=False;ready=False
 while True:
  raw=sys.stdin.buffer.readline(65538)
  if not raw:return
  if len(raw)>65537 or not raw.endswith(b'\n'):
   while raw and not raw.endswith(b'\n'):raw=sys.stdin.buffer.readline(65538)
   error(None,32700,'Request framing or size limit');continue
  if not raw.strip():continue
  if len(raw)-1>65536:error(None,32700,'Request size limit');continue
  try:req=json.loads(raw.decode('utf-8'),object_pairs_hook=pairs,parse_constant=reject_constant)
  except(ValueError,UnicodeError,RecursionError):error(None,32700,'Invalid JSON or parser limit');continue
  if type(req)is not dict:error(None,32600,'Expected one JSON RPC object');continue
  id=req.get('id');has_id='id'in req
  if type(id)is str:
   try:id.encode('utf-8')
   except UnicodeError:error(None,32600,'Invalid Unicode id');continue
  if has_id and not(type(id)is int and len(str(id))<=21 or type(id)is str and len(id.encode('utf-8'))<=256):error(None,32600,'Bounded string or integer id required');continue
  if req.get('jsonrpc')!='2.0'or type(req.get('method'))is not str:error(id,32600,'Invalid JSON RPC envelope');continue
  method=req['method'];params=req.get('params')
  if not has_id:
   if method=='notifications/initialized'and initialized and params in(None,{}):ready=True
   continue
  if params is not None and type(params)is not dict:error(id,32602,'Params must be an object');continue
  if method=='initialize':
   if initialized:error(id,32600,'Session already initialized');continue
   if type(params)is not dict or type(params.get('protocolVersion'))is not str or type(params.get('capabilities'))is not dict or type(params.get('clientInfo'))is not dict:error(id,32602,'Initialize params required');continue
   if type(params['clientInfo'].get('name'))is not str or type(params['clientInfo'].get('version'))is not str:error(id,32602,'Client name and version required');continue
   initialized=True;reply(id,dict(protocolVersion='2025-11-25',capabilities=dict(tools={}),serverInfo=dict(name=server,version=version)));continue
  if method=='ping':reply(id,{});continue
  if not ready:error(id,32600,'Initialize session first');continue
  if method=='tools/list':
   if params not in(None,{}):error(id,32602,'Expected empty params');continue
   reply(id,dict(tools=[dict(name=tool,description=description,inputSchema=dict(type='object',properties={},additionalProperties=False),annotations=dict(readOnlyHint=True,destructiveHint=False,idempotentHint=True,openWorldHint=False))]));continue
  if method=='tools/call':
   if type(params)is not dict or set(params)!=set(('name','arguments'))or params['name']!=tool or type(params['arguments'])is not dict or params['arguments']:error(id,32602,'Unknown tool or invalid arguments');continue
   try:
    result=callback()
    if type(result)is not dict:raise ValueError('callback requires object')
    json.dumps(result,ensure_ascii=False,allow_nan=False).encode('utf-8')
    encoded=json.dumps(result,ensure_ascii=True,separators=(',',':'),allow_nan=False).encode()
    if len(encoded)>65536:raise ValueError('output limit')
   except Exception as exc:reply(id,dict(isError=True,content=[dict(type='text',text='Tool execution failed.')]));continue
   reply(id,dict(isError=False,content=[dict(type='text',text='Read completed.')],structuredContent=result));continue
  error(id,32601,'Unknown method')
