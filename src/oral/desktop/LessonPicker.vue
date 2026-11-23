<script setup>
import {computed} from 'vue'

const props = defineProps({lessons:Array, selected:String, busy:Boolean, itemLabel:String})
const emit = defineEmits(['choose'])
const sections = [
  ['textbook','教材原声'], ['adapted','教材原题改编'], ['theme','主题拓展'], ['local','其他本机课包'],
]
const groups = computed(() => sections.map(([id,label]) => ({
  id,label, rows:props.lessons.filter(row => (row.group || 'local') === id),
})).filter(group => group.rows.length))

function choose(event) {
  const next = event.target.value
  event.target.value = props.selected
  emit('choose',next)
}

function label(row) {
  const prefix = row.number ? '第 '+row.number+' 课 · ' : row.unit ? '第 '+row.unit+' 单元 · ' : ''
  const count = Number.isInteger(row.count) ? ' · '+row.count+' '+props.itemLabel : ''
  return prefix + (row.title?.zh || row.label) + count
}
</script>

<template>
  <div class="lesson-picker">
    <p v-if="!lessons.length" role="status">当前没有可用课包。</p>
    <label v-else>练习课次 <small>共 {{ lessons.length }} 个课包</small>
      <select :value="selected" :disabled="busy" @change="choose">
        <optgroup v-for="group in groups" :key="group.id" :label="group.label">
          <option v-for="row in group.rows" :key="row.id" :value="row.id">{{ label(row) }}</option>
        </optgroup>
      </select>
    </label>
  </div>
</template>

<style scoped>
.lesson-picker { margin: 14px 0; }
.lesson-picker small { margin-left: 8px; color: var(--sub); }
.lesson-picker select { display: block; margin-top: 6px; width: 100%; max-width: 32rem; }
</style>
