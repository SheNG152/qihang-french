import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {zipSync} from 'fflate';

const app=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const appName=JSON.parse(await fs.readFile(path.join(app,'src/manifest.json'),'utf8')).name;
const startName=`启动${appName}.bat`;
const output=path.join(app,'分享版'),web=path.join(output,'网页');
await fs.access(path.join(app,'dist/build/h5/index.html'));
await fs.mkdir(output,{recursive:true});
// Replace only the generated web resources; never copy browser profiles or backups.
if((await fs.realpath(output)).toLowerCase()!==output.toLowerCase())throw new Error('分享目录不能指向项目外部');
await fs.cp(path.join(app,'native/build/windows-host'),path.join(output,'口语运行'),{recursive:true});
await fs.rm(path.join(output,'server.ps1'),{force:true});
const previousWeb=await fs.lstat(web).catch(error=>{if(error.code!=='ENOENT')throw error;return null;});
if(path.dirname(web)!==output||previousWeb?.isSymbolicLink())throw new Error('网页资源路径无效');
await fs.rm(web,{recursive:true,force:true});
await fs.cp(path.join(app,'dist/build/h5'),web,{recursive:true,filter:source=>!/[\\/]static[\\/]lexicon[\\/]audio[\\/][a-f0-9]{64}\.mp3$/.test(source)});
const start=await fs.readFile(path.join(app,'launcher/start.bat'),'utf8');
await fs.writeFile(path.join(output,startName),start.replace(/\r?\n/g,'\r\n'),'utf8');
await fs.copyFile(path.join(app,'SOURCES.md'),path.join(output,'SOURCES.md'));
for(const name of ['LICENSE','COPYRIGHT'])await fs.copyFile(path.join(app,name),path.join(output,name));
const guide=await fs.readFile(path.join(app,'docs/使用教程.md'),'utf8');
const plainGuide=guide.replace(/^#{1,3} /gm,'').replace(/^```.*$/gm,'').replace(/`/g,'').replace(/\*\*/g,'');
await fs.writeFile(path.join(output,'使用说明.txt'),'\uFEFF'+plainGuide.replace(/\r?\n/g,'\r\n'),'utf8');
await fs.copyFile(path.join(app,'src/static/使用教程.html'),path.join(output,'使用教程.html'));

const launch=`@echo off\r\nchcp 65001 >nul\r\nstart "" "%~dp0分享版\\${startName}"\r\n`;
await fs.writeFile(path.join(app,startName),launch,'utf8');
await fs.writeFile(path.join(app,'启动启航法语.bat'),launch,'utf8');
// Package an explicit allowlist, so unrelated files or exported learning backups
// accidentally placed alongside the program can never enter the share archive.
const archiveFiles={};
async function addFile(relative){archiveFiles[appName+'/'+relative.replaceAll('\\','/')]=new Uint8Array(await fs.readFile(path.join(output,relative)));}
async function addWeb(directory='网页'){
  for(const entry of await fs.readdir(path.join(output,directory),{withFileTypes:true})){
    const relative=path.join(directory,entry.name);
    if(entry.isSymbolicLink())throw new Error('分享资源不能包含外部链接');
    if(entry.isDirectory())await addWeb(relative);else await addFile(relative);
  }
}
await addWeb();
await addWeb('口语运行');
for(const name of [startName,'使用说明.txt','使用教程.html','SOURCES.md','LICENSE','COPYRIGHT'])await addFile(name);
const archive=path.join(app,`${appName}_分享版.zip`);
await fs.writeFile(archive,zipSync(archiveFiles,{level:6}));
console.log('分享版已生成：'+output);
console.log(`分享包已生成：${archive}（${Object.keys(archiveFiles).length} 个文件）`);
