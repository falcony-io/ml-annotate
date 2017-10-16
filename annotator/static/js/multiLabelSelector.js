import axios from 'axios';
import moment from 'moment';
import sortedPairs from 'lodash-sorted-pairs'
import React from 'react';
import ReactDOM from 'react-dom';
import ReactTable from 'react-table';
import _ from 'lodash';


class MultiLabelSelector extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      selected: new Set()
    };
    this.keyBindings = {};
  }

  componentDidMount() {
    this.keyBindings['submit'] = () => this.formInput.submit();
    window.Mousetrap.bind('enter', this.keyBindings['submit']);
    this.props.labels.map((label, i) => {
      this.keyBindings[label.id] = () => this.selectLabel(label.id);
      window.Mousetrap.bind('' + (i + 1), this.keyBindings[label.id] );
    });
  }
  componentWillUnmount() {
    this.props.labels.map((label, i) => {
      window.Mousetrap.unbind('' + (i + 1), this.keyBindings[label.id]);
    });
    window.Mousetrap.unbind('enter', this.keyBindings['submit']);
  }

  selectLabel(labelId, e) {
    if (e) {
      e.preventDefault();
    }

    const newSet = new Set(this.state.selected);
    if (newSet.has(labelId)) {
      newSet.delete(labelId);
    } else {
      newSet.add(labelId);
    }
    this.setState({
      selected: newSet
    });

    if (this.props.config.classification_type === 'multi-class') {
      setTimeout(() => this.formInput.submit(), 100);
    }
  }

  render() {
    return <div className="multi-label-selector">
      <form action="#" method="POST" ref={(input) => { this.formInput = input; }}>
        <input type="hidden" name="data_id" value={ this.props.config.data_id } />
        {this.props.labels.map(x => (
          <input key={x.id} type="hidden" name={'label_' + x.id} value={this.state.selected.has(x.id) ? 'yes' : 'no'} />
        ))}

        <h3>{
          {
            'multi-label': 'Choose multiple labels',
            'multi-class': 'Choose a single label'
          }[this.props.config.classification_type]
        }</h3>
        <div className="labels">
          {this.props.labels.map((x, i) => (
            <a key={x.id} href="#" onClick={this.selectLabel.bind(this, x.id)} className={this.state.selected.has(x.id) ? 'selected color-' + x.order_index : 'color-' + x.order_index}>
              <span className="help">{this.state.selected.has(x.id) ? <i className="glyphicon glyphicon-ok"></i> : <i className="glyphicon glyphicon-remove"></i>}</span>
              <span className="name">{x.name}</span>
              {i <= 9 ? <span className="keybinding">{(i+1)}</span> : ''}
            </a>
          ))}
        </div>
        { this.props.config.classification_type === 'multi-label' ? (
          <button type="submit" className="button">Label</button>
        ) : (
          <button type="submit" className="button button-no-category">No category (enter)</button>
        )}
      </form>
    </div>;
  }
}

function renderMultiLabelSelector(elementID, data, config) {
  ReactDOM.render(<MultiLabelSelector labels={data} config={config} />, document.getElementById(elementID));
}

export default renderMultiLabelSelector;
