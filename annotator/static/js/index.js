var $ = require('jquery');
window.$ = $; // Thanks Bootstrap!

import axios from 'axios';
import bootstrap from 'bootstrap';
import hljs from 'highlight.js';
import mousetrap from 'mousetrap';
import renderPlot from './plot';
import renderDataset from './dataset';
import renderMultiLabelSelector from './multiLabelSelector';
import renderProcessedJobs from './processedJobs';

if (document.getElementById('button1')) {
  Mousetrap.bind('1', function() { document.getElementById('button1').click(); });
  Mousetrap.bind('2', function() { document.getElementById('button2').click(); });
  Mousetrap.bind('3', function() { document.getElementById('button3').click(); });
}
hljs.initHighlightingOnLoad();
window.annotate = {
  renderPlot,
  renderDataset,
  renderMultiLabelSelector,
  renderProcessedJobs,
  fetchTrainLog(problemId) {
    axios.get(`/${problemId}/train_log`).then(response => {
      $('.train-log').html(response.data);
    });
  }
};
