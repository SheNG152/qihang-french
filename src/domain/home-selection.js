import {packageKey} from './learning.js';

export function rememberHomeSelection(data,bookId,lessonKey=''){
 const selections=data.lessonSelections||={};
 const previous=data.homeSelection;
 if(previous?.bookId&&previous.lessonKey)selections[previous.bookId]=previous.lessonKey;
 data.homeSelection={bookId,lessonKey};
 selections[bookId]=lessonKey;
}

export function rememberedLesson(data,bookId,lessons){
 const key=data.lessonSelections?.[bookId]??(data.homeSelection?.bookId===bookId?data.homeSelection.lessonKey:'');
 return lessons.find(p=>p.book.id===bookId&&packageKey(p)===key)||null;
}
