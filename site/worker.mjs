import {execute} from './riverflow.mjs';
self.onmessage=({data})=>{try{postMessage({ok:true,result:execute(data.source,data.inputs)});}catch(e){postMessage({ok:false,error:e.message});}};
