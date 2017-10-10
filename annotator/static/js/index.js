var $ = require('jquery');
window.$ = $; // Thanks Bootstrap!

import bootstrap from 'bootstrap';
import hljs from 'highlight.js';
import mousetrap from 'mousetrap';
import renderPlot from './plot';
import renderDataset from './dataset';
import renderMultiLabelSelector from './multiLabelSelector';
import renderProcessedJobs from './processedJobs';

Mousetrap.bind('1', function() { document.getElementById('button1').click(); });
Mousetrap.bind('2', function() { document.getElementById('button2').click(); });
Mousetrap.bind('3', function() { document.getElementById('button3').click(); });
hljs.initHighlightingOnLoad();
window.annotate = {
  renderPlot,
  renderDataset,
  renderMultiLabelSelector,
  renderProcessedJobs
};
