<script setup>
defineProps({ modelValue: { type: Number, default: 0 }, readonly: Boolean })
defineEmits(['update:modelValue'])
</script>
<template>
  <span><button v-for="n in 5" :key="n" type="button" class="star" :disabled="readonly"
    @click="$emit('update:modelValue', n)">{{ n <= modelValue ? '★' : '☆' }}</button></span>
</template>
