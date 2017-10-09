var $ = require('jquery');
window.$ = $; // Thanks Bootstrap!

import bootstrap from 'bootstrap';
import hljs from 'highlight.js';
import renderPlot from './plot';
import renderDataset from './dataset';
import renderMultiLabelSelector from './multiLabelSelector';
import renderProcessedJobs from './processedJobs';

hljs.initHighlightingOnLoad();
window.annotate = {
  renderPlot,
  renderDataset,
  renderMultiLabelSelector,
  renderProcessedJobs
};
