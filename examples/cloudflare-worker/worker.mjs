import module from './sum.wasm';
import {makeHandler} from './handler.mjs';
export default {fetch:makeHandler(module)};
