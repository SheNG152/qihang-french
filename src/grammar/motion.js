// Measure only on open/close; no timers or persistent inline heights.
function clear(el){el.style.removeProperty('height');el.style.removeProperty('opacity');el.style.removeProperty('overflow');}
export const foldTransition={
 onBeforeEnter(el){el.style.height='0px';el.style.opacity='0';el.style.overflow='hidden';},
 onEnter(el){void el.offsetHeight;el.style.height=el.scrollHeight+'px';el.style.opacity='1';},
 onAfterEnter:clear,
 onEnterCancelled:clear,
 onBeforeLeave(el){el.style.height=el.getBoundingClientRect().height+'px';el.style.overflow='hidden';},
 onLeave(el){void el.offsetHeight;el.style.height='0px';el.style.opacity='0';},
 onAfterLeave:clear,
 onLeaveCancelled:clear,
};
