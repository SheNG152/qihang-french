export function primaryMeaning(word){
 const first=word?.primaryMeaning||word?.meanings?.[0]||'';
 return String(first).split(/[；;\n]/)[0].trim();
}
