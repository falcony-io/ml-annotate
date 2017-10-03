import Plotly from 'plotly.js/lib/core';
Plotly.register([
    require('plotly.js/lib/scatter'),
]);


function renderPlot(elementID, data) {
  const trace1 = {
    x: data.map(x => x[0]),
    y: data.map(x => x[1]),
    type: 'scatter'
  };

  Plotly.newPlot(elementID, [trace1]);
}

export default renderPlot;
