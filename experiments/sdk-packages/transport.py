"""Derive SDK B typed transport failure handling without changing protocol code."""

def apply(source):
    def replace(old,new):
        nonlocal source
        assert source.count(old)==1,(old[:100],source.count(old))
        source=source.replace(old,new,1)
    replace('''fn mcp_bytes(p,n)
 let done=0
 while done<n
  let sent=write(1,p+done,n-done)
  if (sent==0)|(sent>>63)
   do exit(1)
  end
  set done=done+sent
 end
 return done
end''','''fn mcp_bytes(p,n)
 let state=buffer("sdk_mcp_transport_error",8)
 if load64(state)!=0
  return 0
 end
 handle io_write_all(1,p,n)
 ok written
  return written
 err write_error
  do store64(state,write_error)
 end
 return 0
end''')
    replace('''   if size>>63
    do exit(1)
   end''','''   if size>>63
    do store64(buffer("sdk_mcp_transport_error",8),0-size)
    return 0
   end''')
    replace(''' let bytes=mcp_line()
 while bytes
  do mcp_request(bytes,server,version,tool,description)
  set bytes=mcp_line()
 end
 return ok(0)
end''',''' # Borrow stdout's descriptor policy only for this ordinary serving call.
 # Darwin fcntl92: GETNOSIGPIPE74, SETNOSIGPIPE73. No global signal handler.
 let transport=buffer("sdk_mcp_transport_error",8)
 do store64(transport,0)
 let previous=syscall6(92,1,74,0,0,0,0)
 if previous>>63
  return err(0-previous)
 end
 let quiet=syscall6(92,1,73,1,0,0,0)
 if quiet>>63
  return err(0-quiet)
 end
 let bytes=mcp_line()
 while bytes
  do mcp_request(bytes,server,version,tool,description)
  if load64(transport)==0
   set bytes=mcp_line()
  else
   set bytes=0
  end
 end
 let failure=load64(transport)
 let restored=syscall6(92,1,73,previous,0,0,0)
 if failure
  return err(failure)
 end
 if restored>>63
  return err(65536-restored)
 end
 return ok(0)
end''')
    return source
