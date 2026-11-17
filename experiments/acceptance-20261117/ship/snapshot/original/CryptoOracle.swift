import Foundation
import CryptoKit
import Darwin
setbuf(stdout,nil)
func unhex(_ s:String)->Data { var a=[UInt8](); var i=s.startIndex; while i<s.endIndex { let j=s.index(i,offsetBy:2); a.append(UInt8(s[i..<j],radix:16)!);i=j };return Data(a) }
func hex(_ d:Data)->String {d.map{String(format:"%02x",$0)}.joined()}
while let line=readLine(){do{
 let v=try JSONSerialization.jsonObject(with:Data(line.utf8)) as! [String:String]
 let k=SymmetricKey(data:unhex(v["key"]!));let nonce=try ChaChaPoly.Nonce(data:unhex(v["nonce"]!));let aad=unhex(v["aad"]!);let data=unhex(v["data"]!)
 let out:[String:String]
 if v["op"]=="open" {let box=try ChaChaPoly.SealedBox(nonce:nonce,ciphertext:data,tag:unhex(v["tag"]!));let p=try ChaChaPoly.open(box,using:k,authenticating:aad);out=["data":hex(p)]}
 else {let b=try ChaChaPoly.seal(data,using:k,nonce:nonce,authenticating:aad);out=["data":hex(b.ciphertext),"tag":hex(b.tag)]}
 print(String(data:try JSONSerialization.data(withJSONObject:out,options:.sortedKeys),encoding:.utf8)!)}catch{print("{\"error\":\"authentication-or-input\"}")}}
