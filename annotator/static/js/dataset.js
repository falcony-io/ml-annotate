import axios from 'axios';
import moment from 'moment';
import mousetrap from 'mousetrap';
import sortedPairs from 'lodash-sorted-pairs'
import React from 'react';
import ReactDOM from 'react-dom';
import ReactTable from 'react-table';
import _ from 'lodash';



class Dataset extends React.Component {
  constructor(props) {
    super(props);

    const dynamicMetaColumns = _.uniq(_.flatten(
      this.props.data.map(x => x[4] || {}).map(Object.keys)
    ));

    this.problemLabelsAsDict = _.fromPairs(this.props.problemLabels);
    this.problemLabelsIndex = _.fromPairs(this.props.problemLabels.map((x, i) => [x[0], i]));
    this.state = {
      data: props.data.map(x => ({
        id: x[0],
        freeText: x[1],
        entityId: x[2],
        tableName: x[3],
        meta: x[4],
        probability: x[5] || {},
        sortValue: x[6],
        labels: x[7] || [],
        labelCreatedAt: x[8]
      })),
      selectedIds: new Set(),
      selectedLabel: this.props.problemLabels[0][0],
      dynamicMetaColumns,
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
          filterable: false,
          Cell: row => {
            const contents = row.value || {};
            return _.orderBy(_.toPairs(contents), 1, 'desc').map(([label, probability]) => (
              <div className={'dataset-probability ' + (
                  probability && probability > 0.5 ? 'probable color-' + this.problemLabelsIndex[label] : 'not-probable font-color-' + this.problemLabelsIndex[label]
                )} key={label}>
                <span className="dataset-probability-key">{this.problemLabelsAsDict[label]}</span>:
                <span className="dataset-probability-value">{probability ? Math.round(probability*1000)/10 : 'n/a'} %</span>
              </div>
            ));
          },
          show: false
        },
        { Header: 'Sort value', accessor: 'sortValue', show: false },
        {
          Header: 'Labels',
          accessor: 'labels',
          width: 200,
          Cell: row => (
            <div>
              {row.value === null || !row.value.length ? <span className="badge-no-labels">no labels</span>: ''}
              {
                this.props.classificationType === 'multi-class' &&
                row.value &&
                row.value.length &&
                row.value.every(([key, value]) => !value) ? <span className="badge-no-category">No category</span> : ''}
              {(row.value || []).map(([key, value], index) => {
                const label = this.problemLabelsAsDict[key];

                if (this.props.classificationType === 'multi-class') {
                  if (value === true) return <span key={index} className={'badge color-' + this.problemLabelsIndex[key]} title="Labeled as true">✓ {label}</span>;
                } else {
                  if (value === true) return <span key={index} className="badge color-yes" title="Labeled as true">✓ {label}</span>;
                  else if (value === false) return <span key={index} className="badge color-no" title="Labeled as false">× {label}</span>;
                  else if (value === null) return <span key={index} className="badge color-skip" title="Skipped label">? {label}</span>;
                  else return <span key={index} className="badge">Unknown {value}</span>;
                }
              })}
            </div>
          ),
          filterMethod: (filter, row) => {
            if (filter.value === 'all') {
              return true;
            } else if (filter.value === 'none') {
              return row[filter.id] === null || !row[filter.id].length;
            } else if (filter.value === 'all_false') {
              return row[filter.id] && row[filter.id].length && row[filter.id].every(x => !x[1])
            } else if (String(filter.value).includes(':')) {
              const [key, value] = filter.value.split(':');
              const expected = {
                'true': true,
                'false': false,
                'skip': null
              }[value];
              return row[filter.id] && row[filter.id].some(
                x => x[0] === key && x[1] == expected
              );
            }
          },
          Filter: ({ filter, onChange }) => (
            <select
              onChange={event => onChange(event.target.value)}
              style={{ width: "100%" }}
              value={filter ? filter.value : "all"}
            >
              <option value="all">All</option>
              {
                this.props.problemLabels.map(([id, label]) => {
                  return [
                    <option key={'A' + id} value={id + ':true'}>{label}: True</option>,
                    <option key={'B' + id} value={id + ':false'}>{label}: False</option>,
                    <option key={'C' + id} value={id + ':skip'}>{label}: Skip</option>,
                  ];
                })
              }
              <option value="all_false">All labels marked as false</option>
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
              <input className="mousetrap" type="checkbox" onChange={this.selectId.bind(this, row.original.id)} checked={this.state.selectedIds.has(row.original.id)} />
            </label>
          ),
          width: 32
        },
        {
          Header: 'Label created',
          accessor: 'labelCreatedAt',
          filterable: false,
          minWidth: 70,
          Cell: row => (
            <span title={row.value}>{row.value === null ? '' : moment(row.value).fromNow()}</span>
          ),
          show: false
        },
      ]
    };
    for (let dynamicColumn of dynamicMetaColumns) {
      this.state.columns.push({
        Header: `meta: ${dynamicColumn}`,
        accessor: `meta.${dynamicColumn}`,
        show: false
      })
    }
    for (let label of this.props.problemLabels) {
      this.state.columns.push({
        id: `x.probability.${label[0]}`,
        Header: `probability: ${label[1]}`,
        accessor: x => x.probability[label[0]],
        show: false,
        Cell: row => <span>{row.value === undefined ? 'n/a' : Math.round(row.value*1000)/10} %</span>
      })
    }
    for (let column of this.state.columns) {
      column.show = column.show === undefined ? true : column.show;
    }
  }

  componentDidMount() {
    this.keyBindings = {};
    this.props.problemLabels.map((label, i) => {
      this.keyBindings[''+(i+1)] = this.shortcutForLabeling.bind(this, i);
      mousetrap.bind(''+(i+1), this.keyBindings[''+(i+1)]);
    });

    if (this.props.classificationType === 'multi-class') {
      this.keyBindings['0'] = this.shortcutForLabeling.bind(this, 'no_category');
      mousetrap.bind('0', this.keyBindings['0']);
    } else {
      this.keyBindings['0'] = this.shortcutForLabeling.bind(this, 'false');
      mousetrap.bind('0', this.keyBindings['0']);
    }
  }

  componentWillUnmount() {
    for (const [key, func] of Object.entries(this.keyBindings)) {
      mousetrap.unbind(key, func);
    }
    this.keyBindings = {};
  }

  shortcutForLabeling(i) {
    if (i === 'no_category') {
      this.setState({
        selectedLabel: i
      });
      this.markSelectedAs(true, null);
    } else if (i === 'false') {
      this.setState({
        selectedLabel: this.props.problemLabels[0][0]
      });
      this.markSelectedAs(false, null);
    } else {
      this.setState({
        selectedLabel: this.props.problemLabels[i][0]
      });
      this.markSelectedAs(true, null);
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
    const props = this.props;

    if (e) {
      e.preventDefault();
    }

    if (this.state.selectedIds.size >= 50) {
      if (!confirm(`This will change ${this.state.selectedIds.size} labels. Are you sure?`)) {
        return;
      }
    }

    function changeLabel(previous, labelId, newValue) {
      if (props.classificationType === 'multi-class') {
        if (newValue === undefined) return [];
        else if (labelId == 'no_category') return [[labelId, false]];
        else return [[labelId, newValue]];
      }
      const arr = previous.filter(([key, value]) => key !== labelId);

      if (newValue !== undefined) {
        arr.push([labelId, newValue]);
      }
      return arr;
    }

    const problemId = window.location.pathname.split('/')[1];
    const post = props.classificationType === 'multi-class' ? (
      (axios.post(`/${problemId}/multi_class_batch_label`, {
        label: value === 'undo' ? 'undo' : this.state.selectedLabel,
        selectedIds: Array.from(this.state.selectedIds),
      }))
    ) : (axios.post(`/${problemId}/batch_label`, {
      label: this.state.selectedLabel,
      selectedIds: Array.from(this.state.selectedIds),
      value: value
    }));

    post.then((response) => {
      const newData = this.state.data.slice();

      for (const [i, item] of this.state.data.entries()) {
        if (this.state.selectedIds.has(item.id)) {
          const clonedItem = Object.assign({}, item);
          if (value === 'undo') {
            clonedItem.labels = changeLabel(clonedItem.labels, this.state.selectedLabel);
          } else {
            clonedItem.labels = changeLabel(clonedItem.labels, this.state.selectedLabel, value);
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

  changeSelectedLabel(e) {
    this.setState({
      selectedLabel: e.target.value
    });
  }

  render() {
    const data = this.state.data;

    return (
      <div>
          <div className="data-batch-label">
            <div className="data-batch-label-selected">{this.state.selectedIds.size} selected</div>
            {this.state.selectedIds.size > 0 ? [
                <div key="a">
                  <select value={this.state.selectedLabel} onChange={this.changeSelectedLabel.bind(this)}>
                    {this.props.problemLabels.map(([key, name]) => {
                      return <option key={key} value={key}>{name}</option>;
                    })}
                    {this.props.classificationType === 'multi-class' ? (
                      <option key="no_category" value="no_category">No category</option>
                    ) : ''}
                  </select>
                </div>,
                <div key="b">
                  <a href="#" className="color-yes" onClick={this.markSelectedAs.bind(this, true)}>{this.props.classificationType === 'multi-class' ? 'Categorize' : 'Mark as true'}</a>
                  {this.props.classificationType === 'multi-class' ? '' : (
                    <span>
                      <a href="#" className="color-no" onClick={this.markSelectedAs.bind(this, false)}>Mark as false</a>
                      <a href="#" className="color-skip" onClick={this.markSelectedAs.bind(this, null)}>Mark as skip</a>
                    </span>
                  )}
                  <a href="#" className="color-special" onClick={this.markSelectedAs.bind(this, 'undo')}>Remove labels</a>
                  <a href="#" className="color-special" onClick={this.clearSelection.bind(this)}>Select none</a>
                </div>
            ]: (
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
            return row[id] !== undefined ? stringValue.toLowerCase().includes(filter.value.toLowerCase()) : false;
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
        <div className="floating-keyboard-shortcuts">
          <h5>Keyboard shorcuts</h5>
          {this.props.problemLabels.map((x, i) => {
            return <div key={i}><span className="badge">{i+1}</span>{x[1]}</div>;
          })}
          <div><span className="badge">0</span>no category<br /></div>
        </div>
      </div>
    );
  }
}

function renderDataset(elementID, data, config) {
  ReactDOM.render(<Dataset data={data} problemLabels={config.problem_labels} classificationType={config.classification_type} />, document.getElementById(elementID));
}

export default renderDataset;
