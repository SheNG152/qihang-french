<script setup>
import PracticeSkills from './PracticeSkills.vue'

defineProps({dailyHref:String, examLevel:{type:String,default:'DELF A1'}})
const emit = defineEmits(['daily','exam'])
const bars = [25,45,68,43,80,96,72,47,68,40,24]
const examSkills = {focus:['听题理解','临场应答','组织表达'],support:['词形准确']}
</script>

<template>
  <section class="practice-home">
    <p class="overline" lang="fr">Atelier de français</p>
    <h1>口语练习室</h1>
    <div class="mode-grid">
      <component :is="dailyHref?'a':'button'" class="mode daily" :type="dailyHref?undefined:'button'"
        :href="dailyHref" :target="dailyHref?'_blank':undefined" :rel="dailyHref?'noopener':undefined"
        aria-labelledby="daily-practice-title" @click="emit('daily')">
        <span class="card-fr" lang="fr">Pratique</span>
        <span class="bars" aria-hidden="true"><i v-for="(height,index) in bars" :key="index" :style="{'--bar':height+'%'}"/></span>
        <strong id="daily-practice-title">日常练习</strong>
        <span class="card-foot">跟着课本，练好每一句。<b aria-hidden="true">↗</b></span>
      </component>
      <button type="button" class="mode exam" aria-labelledby="exam-title" aria-describedby="exam-skills exam-summary" @click="emit('exam')">
        <span class="card-fr" lang="fr">Examen</span>
        <span class="exam-label">{{ examLevel }}</span>
        <strong id="exam-title">考试模拟</strong>
        <PracticeSkills id="exam-skills" v-bind="examSkills"/>
        <span class="skill-key">外圈主练 · 内圈兼练</span>
        <span id="exam-summary" class="card-foot">听考官提问，练习问答和情景互动。<b aria-hidden="true">↗</b></span>
      </button>
    </div>
  </section>
</template>

<style scoped>
.practice-home {
  --sub:#576d66;
  --forest:#194e40;
  padding-top:var(--practice-home-top,clamp(30px,6vh,66px));
  color:#223e38;
  font-family:"Segoe UI","Microsoft YaHei",sans-serif;
}
h1 { margin:0; font-size:clamp(32px,3.6vw,48px); line-height:1.24; letter-spacing:-.035em; }
.overline,.card-fr { font-family:Georgia,"Times New Roman",serif; font-style:italic; }
.overline { margin:0 0 8px; color:var(--sub); font-size:19px; }
.mode-grid { display:grid; grid-template-columns:1.38fr 1fr; gap:18px; margin-top:32px; }
.mode {
  position:relative; display:flex; flex-direction:column; align-items:flex-start;
  box-sizing:border-box; width:100%; min-height:250px; padding:28px 30px; margin:0;
  overflow:hidden; border:1px solid; border-radius:20px;
  font:inherit; color:inherit; text-align:left; text-decoration:none; cursor:pointer;
  transition:box-shadow .18s ease;
}
.mode::after { content:none; }
.mode:hover { box-shadow:0 8px 22px #19382913; }
.mode:focus-visible { outline:3px solid #267653; outline-offset:4px; }
.daily { background:#d9e9da; border-color:#c4dac7; }
.card-fr { font-size:23px; }
.mode strong { z-index:1; margin-top:auto; font-size:clamp(28px,3vw,40px); line-height:1.4; }
.card-foot { display:flex; align-items:center; justify-content:space-between; gap:12px; width:100%; font-size:14px; }
.card-foot b { display:grid; place-items:center; flex-shrink:0; width:40px; height:40px; border-radius:50%; font-size:21px; background:var(--forest); color:white; }
.exam { --skill-ink:#384960; background:#f0f3f7; color:var(--skill-ink); border-color:#d6dfe6; }
.exam strong { margin-top:4px; }
.exam :deep(.practice-skills) { box-sizing:border-box; margin-top:8px; background:#f9fbfe; border:1px solid #dce5ee; border-radius:12px; }
.exam .card-foot b { background:transparent; color:inherit; border:1px solid #afbdc9; }
.exam-label { position:absolute; top:33px; right:26px; padding:6px 9px; border:1px solid #b7c3ce; border-radius:4px; font:12px Georgia,serif; letter-spacing:.12em; }
.skill-key { align-self:center; margin:6px 0 8px; color:var(--sub); font-size:13px; line-height:1.5; }
.bars { position:absolute; top:26px; right:26px; display:flex; align-items:center; gap:4px; height:72px; opacity:.52; }
.bars i { width:3px; height:var(--bar); border-radius:3px; background:#6b997e; }
@media (max-width:880px) {
  .mode-grid { grid-template-columns:1.15fr 1fr; }
  .bars { height:44px; gap:2px; }
}
@media (max-width:620px) {
  .mode-grid { grid-template-columns:1fr; }
  .mode { min-height:175px; padding:20px; }
  .exam-label { top:23px; right:20px; }
}
</style>
