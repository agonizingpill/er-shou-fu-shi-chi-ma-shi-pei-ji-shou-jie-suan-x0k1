import{esc}from'../utils/format.js';import{STATES}from'../constants.js';
export const money=v=>'¥'+(v/100).toFixed(2);
export const badge=s=>`<span class="status ${esc(s)}">${esc(STATES[s]||s)}</span>`;
export const heading=(n,t,d)=>`<div class="heading"><div class="measure-index">${n}<span>cm</span></div><div><small>HESHEN WARDROBE / 合身衣橱</small><h1>${t}</h1><p>${d}</p></div></div>`;
export const tag=g=>`<div class="garment-tag"><small>${esc(g.code)}</small><b>${esc(g.title)}</b>${badge(g.state)}<em>${money(g.price_cents)}</em><p>${esc(g.condition)}</p></div>`;
export const form=(id,title,endpoint,body)=>`<form id="${id}" data-endpoint="${endpoint}"><h3>${title}</h3>${body}<button>记入寄售簿</button></form>`;
export const input=(n,label,value='',type='text')=>`<label>${label}<input name="${n}" value="${esc(value)}" type="${type}" ${type==='number'?'step="any"':''} required></label>`;
export const select=(n,label,options)=>`<label>${label}<select name="${n}">${options}</select></label>`;
export const area=(n,label,value='')=>`<label>${label}<textarea name="${n}" required>${esc(value)}</textarea></label>`;
