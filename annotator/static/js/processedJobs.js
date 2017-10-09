import axios from 'axios';
import moment from 'moment';
import sortedPairs from 'lodash-sorted-pairs'
import React from 'react';
import ReactDOM from 'react-dom';
import ReactTable from 'react-table';
import _ from 'lodash';



class ProcessedJobs extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      data: props.data.map(x => ({
        id: x[0],
        accuracy: x[1],
        createdAt: x[2]
      })),
      columns: [
        { Header: 'ID', accessor: 'id' },
        {
          Header: 'Accuracy',
          accessor: 'accuracy',
          Cell: x => <span>{Math.round(x.value*1000)/10} %</span>
        },
        {
          Header: 'Created At',
          accessor: 'createdAt',
          filterable: false,
          minWidth: 70,
          Cell: row => (
            <span title={row.value}>{row.value === null ? '' : moment(row.value).fromNow()}</span>
          )
        },
      ]
    };
  }

  render() {
    const data = this.state.data;

    return (
      <div>
        <ReactTable
          filterAll={true}
          sortable={true}
          resizable={true}
          filterable={true}
          defaultFilterMethod={(filter, row, column) => {
            const id = filter.pivotId || filter.id;
            const stringValue = typeof row[id] === 'object' ? JSON.stringify(row[id]) : String(row[id]);
            return row[id] !== undefined ? stringValue.toLowerCase().includes(filter.value.toLowerCase()) : false;
          }}
          resizable={true}
          data={data}
          columns={this.state.columns}
        >
            {(state, makeTable, instance) => {
              return (
                <div>
                  {makeTable()}
                </div>
              )
            }}
        </ReactTable>
      </div>
    );
  }
}

function renderProcessedJobs(elementID, data) {
  ReactDOM.render(<ProcessedJobs data={data} />, document.getElementById(elementID));
}

export default renderProcessedJobs;
