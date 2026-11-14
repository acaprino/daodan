const leftPad = require('left-pad');

const map = window.L.map('map').setView([45.07, 7.69], 12);
document.title = leftPad(String(map.getZoom()), 3, '0');
