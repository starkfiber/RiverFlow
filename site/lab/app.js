/* ES5 host glue. Modern path executes RF2-emitted WASM; compatibility is a limited JS sum. */
(function () {
  'use strict';
  var instance = null;
  var available = false;
  function el(id) { return document.getElementById(id); }
  function values(text) {
    var parts, data = [], i, value;
    if (text.length > 12288) { throw new Error('Input is too long.'); }
    if (text === '') { return data; }
    parts = text.split(',');
    if (parts.length > 1024) { throw new Error('Use at most 1,024 values.'); }
    for (i = 0; i < parts.length; i += 1) {
      if (!/^(0|[1-9][0-9]{0,9})$/.test(parts[i])) { throw new Error('Use whole numbers such as 19,23.'); }
      value = Number(parts[i]);
      if (value > 4294967295) { throw new Error('A value exceeds the unsigned 32-bit limit.'); }
      data.push(value);
    }
    return data;
  }
  function compat(data) {
    var total = 0, i;
    for (i = 0; i < data.length; i += 1) {
      if (total + data[i] > 4294967295) { return { value: 0, status: 4, work: 3 + 3 * (i + 1) }; }
      total += data[i];
    }
    return { value: total, status: 0, work: 3 + 3 * data.length };
  }
  function compute(data, force) {
    var result;
    if (available && !force) {
      new Uint32Array(instance.exports.memory.buffer).set(data);
      result = { value: instance.exports.run(0, data.length, data.length) >>> 0,
        status: instance.exports.status(), work: instance.exports.work() };
      result.engine = 'RF2 compiled WebAssembly';
    } else { result = compat(data); result.engine = 'Compatibility JavaScript sum'; }
    return result;
  }
  el('form').onsubmit = function (event) {
    var result;
    if (event && event.preventDefault) { event.preventDefault(); }
    try {
      result = compute(values(el('values').value), el('mode').value === 'compat');
      el('engine').textContent = result.engine;
      el('answer').textContent = result.status === 0 ? String(result.value) : 'Overflow refused';
      el('details').textContent = 'Status ' + result.status + ' · Abstract work events ' + result.work + '. These are not CPU cycles.';
    } catch (error) {
      el('answer').textContent = 'Check your input';
      el('details').textContent = error.message;
    }
    return false;
  };
  if (typeof WebAssembly !== 'undefined' && typeof WebAssembly.Module === 'function' && typeof XMLHttpRequest !== 'undefined') {
    var xhr = new XMLHttpRequest();
    xhr.open('GET', 'sum.wasm', true);
    xhr.responseType = 'arraybuffer';
    xhr.onload = function () {
      try {
        if (xhr.status !== 200) { throw new Error('Module unavailable'); }
        instance = new WebAssembly.Instance(new WebAssembly.Module(xhr.response));
        available = true;
        el('engine').textContent = 'Ready: RF2 compiled WebAssembly';
      } catch (error) { el('engine').textContent = 'Ready: compatibility JavaScript sum'; }
    };
    xhr.onerror = function () { el('engine').textContent = 'Ready: compatibility JavaScript sum'; };
    xhr.send(null);
  } else { el('engine').textContent = 'Ready: compatibility JavaScript sum'; }
}());
