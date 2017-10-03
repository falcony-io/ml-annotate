import axios from 'axios';
import React from 'react';
import ReactDOM from 'react-dom';
import ReactTable from 'react-table';
import _ from 'lodash';


class Dataset extends React.Component {
  constructor(props) {
    super(props);

    const dynamicColumns = _.uniq(_.flatten(
      this.props.data.map(x => x[4] || {}).map(Object.keys)
    ));

    this.state = {
      data: props.data.map(x => ({
        id: x[0],
        freeText: x[1],
        entityId: x[2],
        tableName: x[3],
        meta: x[4],
        probability: x[5],
        sortValue: x[6],
        labels: x[7]
      })),
      selectedIds: new Set(),
      dynamicColumns,
      columns: [
        { Header: 'ID', accessor: 'id', show: false },
        {
          Header: 'Text',
          accessor: 'freeText',
          Cell: row => <div className="dataset-free-text">{row.value}</div>,
          minWidth: 300
        },
        { Header: 'EntityID', accessor: 'entityId', show: false },
        { Header: 'Table name', accessor: 'tableName', show: false },
        {
          Header: 'Meta',
          accessor: 'meta',
          Cell: row => {
            const contents = row.value;
            if (!contents) return '';

            var sortedKeys = Object.keys(contents).sort();
            return sortedKeys.map(key => (
              <div className="dataset-meta" key={key}>
                <span className="dataset-meta-key">{key}</span>:
                <span className="dataset-meta-value">{contents[key]}</span>
              </div>
            ));
          },
          show: false
        },
        {
          Header: 'Probability',
          accessor: 'probability',
          Cell: row => <span>{Math.round(row.value*1000)/10} %</span>
        },
        { Header: 'Sort value', accessor: 'sortValue', show: false },
        {
          Header: 'Labels',
          accessor: 'labels',
          width: 100,
          Cell: row => (
            <div>
              {row.value === null ? <span className="badge-no-labels">no labels</span>: ''}
              {(row.value || []).map((x, index) => {
                if (x === true) return <span key={index} className="badge color-yes">true</span>;
                if (x === false) return <span key={index} className="badge color-no">false</span>;
                if (x === null) return <span key={index} className="badge color-skip">skip</span>;
              })}
            </div>
          ),
          filterMethod: (filter, row) => {
            if (filter.value === 'all') {
              return true;
            }
            if (filter.value === 'true') {
              return row[filter.id] && row[filter.id].includes(true);
            }
            if (filter.value === 'false') {
              return row[filter.id] && row[filter.id].includes(false);
            }
            if (filter.value === 'skip') {
              return row[filter.id] && row[filter.id].includes(null);
            }
            if (filter.value === 'none') {
              return row[filter.id] === null || !row[filter.id].length;
            }
          },
          Filter: ({ filter, onChange }) => (
            <select
              onChange={event => onChange(event.target.value)}
              style={{ width: "100%" }}
              value={filter ? filter.value : "all"}
            >
              <option value="all">All</option>
              <option value="true">True</option>
              <option value="false">False</option>
              <option value="skip">Skip</option>
              <option value="none">None</option>
            </select>
          )
        },
        {
          Header: 'Batch label',
          accessor: null,
          filterable: false,
          Cell: row => (
            <label style={{ height: '100%', width: '100%', textAlign: 'center' }}>
              <input type="checkbox" onChange={this.selectId.bind(this, row.original.id)} checked={this.state.selectedIds.has(row.original.id)} />
            </label>
          ),
          width: 32
        }
      ]
    };
    for (let dynamicColumn of dynamicColumns) {
      this.state.columns.push({
        Header: `meta: ${dynamicColumn}`,
        accessor: `meta.${dynamicColumn}`,
        show: false
      })
    }
    for (let column of this.state.columns) {
      column.show = column.show === undefined ? true : column.show;
    }
  }

  selectId(id) {
    const newSet = new Set(this.state.selectedIds);
    if (newSet.has(id)) {
      newSet.delete(id);
    } else {
      newSet.add(id);
    }
    this.setState({
      selectedIds: newSet
    });
  }

  markSelectedAs(value, e) {
    e.preventDefault();

    const problemId = window.location.pathname.split('/')[1];
    axios.post(`/${problemId}/batch_label`, {
      selectedIds: Array.from(this.state.selectedIds),
      value: value
    })
    .then((response) => {
      // const changed = [];
      const newData = this.state.data.slice();

      for (const [i, item] of this.state.data.entries()) {
        if (this.state.selectedIds.has(item.id)) {
          const clonedItem = Object.assign({}, item);
          if (value === 'undo') {
            clonedItem.labels = null;
          } else {
            clonedItem.labels = [value];
          }
          newData[i] = clonedItem;
        }
      }

      this.setState({
        data: newData,
        selectedIds: new Set()
      });
    })
    .catch((error) => {
      console.error(error);
      alert('Error occured when batch changing items');
    });
  }

  toggleColumn(toggleColumn) {
    const newColumns = _.cloneDeep(this.state.columns);
    for (let column of newColumns) {
      if (column.accessor == toggleColumn.accessor) {
        column.show = !column.show;
      }
    }
    this.setState({
      columns: newColumns
    });
  }

  clearSelection(e) {
    e.preventDefault();

    this.setState({
      selectedIds: new Set()
    });
  }

  selectAll(e) {
    e.preventDefault();

    this.setState({
      selectedIds: new Set(this.tableState.sortedData.map(x => x.id))
    });
  }

  render() {
    const data = this.state.data;

    return (
      <div>
          <div className="data-batch-label">
            <div className="data-batch-label-selected">{this.state.selectedIds.size} selected</div>
            {this.state.selectedIds.size > 0 ? (
              <div>
                <a href="#" className="color-yes" onClick={this.markSelectedAs.bind(this, true)}>Mark as true</a>
                <a href="#" className="color-no" onClick={this.markSelectedAs.bind(this, false)}>Mark as false</a>
                <a href="#" className="color-skip" onClick={this.markSelectedAs.bind(this, null)}>Mark as skip</a>
                <a href="#" className="color-special" onClick={this.markSelectedAs.bind(this, 'undo')}>Undo</a>
                <a href="#" className="color-special" onClick={this.clearSelection.bind(this)}>clear</a>
              </div>
            ): (
              <a href="#" className="color-special" onClick={this.selectAll.bind(this)}>Select all</a>
            )}
          </div>
        <div className="data-table-columns">
          {this.state.columns.map(column => (
            <a
              href="#"
              onClick={this.toggleColumn.bind(this, column)}
              key={column.Header}
              className={'column-toggle ' + (column.show ? 'column-show' : 'column-hide')}
            >
              {column.Header}
            </a>
          ))}
        </div>
        <ReactTable
          filterAll={true}
          sortable={true}
          resizable={true}
          filterable={true}
          defaultFilterMethod={(filter, row, column) => {
            const id = filter.pivotId || filter.id;
            const stringValue = typeof row[id] === 'object' ? JSON.stringify(row[id]) : String(row[id]);
            return row[id] !== undefined ? stringValue.toLowerCase().includes(filter.value.toLowerCase()) : true;
          }}
          resizable={true}
          data={data}
          columns={this.state.columns}
        >
            {(state, makeTable, instance) => {
              this.tableState = state;
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

function renderDataset(elementID, data) {
  ReactDOM.render(<Dataset data={data} />, document.getElementById(elementID));
}

export default renderDataset;
