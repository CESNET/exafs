'use strict';

function _defineProperty(obj, key, value) { if (key in obj) { Object.defineProperty(obj, key, { value: value, enumerable: true, configurable: true, writable: true }); } else { obj[key] = value; } return obj; }

function _instanceof(left, right) { if (right != null && typeof Symbol !== "undefined" && right[Symbol.hasInstance]) { return right[Symbol.hasInstance](left); } else { return left instanceof right; } }

function _typeof(obj) { if (typeof Symbol === "function" && typeof Symbol.iterator === "symbol") { _typeof = function _typeof(obj) { return typeof obj; }; } else { _typeof = function _typeof(obj) { return obj && typeof Symbol === "function" && obj.constructor === Symbol && obj !== Symbol.prototype ? "symbol" : typeof obj; }; } return _typeof(obj); }

function _classCallCheck(instance, Constructor) { if (!_instanceof(instance, Constructor)) { throw new TypeError("Cannot call a class as a function"); } }

function _defineProperties(target, props) { for (var i = 0; i < props.length; i++) { var descriptor = props[i]; descriptor.enumerable = descriptor.enumerable || false; descriptor.configurable = true; if ("value" in descriptor) descriptor.writable = true; Object.defineProperty(target, descriptor.key, descriptor); } }

function _createClass(Constructor, protoProps, staticProps) { if (protoProps) _defineProperties(Constructor.prototype, protoProps); if (staticProps) _defineProperties(Constructor, staticProps); return Constructor; }

function _possibleConstructorReturn(self, call) { if (call && (_typeof(call) === "object" || typeof call === "function")) { return call; } return _assertThisInitialized(self); }

function _assertThisInitialized(self) { if (self === void 0) { throw new ReferenceError("this hasn't been initialised - super() hasn't been called"); } return self; }

function _getPrototypeOf(o) { _getPrototypeOf = Object.setPrototypeOf ? Object.getPrototypeOf : function _getPrototypeOf(o) { return o.__proto__ || Object.getPrototypeOf(o); }; return _getPrototypeOf(o); }

function _inherits(subClass, superClass) { if (typeof superClass !== "function" && superClass !== null) { throw new TypeError("Super expression must either be null or a function"); } subClass.prototype = Object.create(superClass && superClass.prototype, { constructor: { value: subClass, writable: true, configurable: true } }); if (superClass) _setPrototypeOf(subClass, superClass); }

function _setPrototypeOf(o, p) { _setPrototypeOf = Object.setPrototypeOf || function _setPrototypeOf(o, p) { o.__proto__ = p; return o; }; return _setPrototypeOf(o, p); }

function sortIp(a, b) {
  a = a.split('/');
  b = b.split('/');
  var num1 = Number(a[0].split(".").map(function (num) {
    return "000".concat(num).slice(-3);
  }).join(""));
  var num2 = Number(b[0].split(".").map(function (num) {
    return "000".concat(num).slice(-3);
  }).join(""));
  return num1 - num2;
}

function sortString(a, b) {
  var nameA = a.toLowerCase(); // ignore upper and lowercase

  var nameB = b.toLowerCase(); // ignore upper and lowercase

  if (nameA < nameB) {
    return -1;
  }

  if (nameA > nameB) {
    return 1;
  } //  must be equal


  return 0;
}

function sortExpires(a, b) {
  var dateA = Date.parse(a);
  var dateB = Date.parse(b);

  if (dateA < dateB) {
    return -1;
  }

  if (dateA > dateB) {
    return 1;
  } //  must be equal


  return 0;
}

var Button =
/*#__PURE__*/
function (_React$Component) {
  _inherits(Button, _React$Component);

  function Button() {
    _classCallCheck(this, Button);

    return _possibleConstructorReturn(this, _getPrototypeOf(Button).apply(this, arguments));
  }

  _createClass(Button, [{
    key: "render",
    value: function render() {
      var link = this.props.link;
      var css = "btn btn-" + this.props.css + " btn-sm";
      var icon = "glyphicon glyphicon-" + this.props.icon;
      return React.createElement("a", {
        className: css,
        href: link,
        role: "button"
      }, React.createElement("span", {
        className: icon
      }));
    }
  }]);

  return Button;
}(React.Component);

var TooltipButton =
/*#__PURE__*/
function (_React$Component2) {
  _inherits(TooltipButton, _React$Component2);

  function TooltipButton() {
    _classCallCheck(this, TooltipButton);

    return _possibleConstructorReturn(this, _getPrototypeOf(TooltipButton).apply(this, arguments));
  }

  _createClass(TooltipButton, [{
    key: "render",
    value: function render() {
      var text = this.props.text;
      return React.createElement("button", {
        type: "button",
        className: "btn btn-info btn-sm",
        "data-toggle": "tooltip",
        "data-placement": "top",
        title: text
      }, React.createElement("span", {
        className: "glyphicon glyphicon-comment"
      }));
    }
  }]);

  return TooltipButton;
}(React.Component);

var RulesRow =
/*#__PURE__*/
function (_React$Component3) {
  _inherits(RulesRow, _React$Component3);

  function RulesRow() {
    _classCallCheck(this, RulesRow);

    return _possibleConstructorReturn(this, _getPrototypeOf(RulesRow).apply(this, arguments));
  }

  _createClass(RulesRow, [{
    key: "render",
    value: function render() {
      var rule = this.props.rule;
      var delete_link = rule.delete_link + '/active/source';
      var time_link = rule.time_link + '/active/source';

      if (this.props.rstate && this.props.sortKey && this.props.filterText) {
        delete_link = rule.delete_link + '/' + this.props.rstate + '/' + this.props.sortKey + '/' + this.props.filterText;
        time_link = rule.time_link + '/' + this.props.rstate + '/' + this.props.sortKey + '/' + this.props.filterText;
      } else if (this.props.rstate && this.props.sortKey) {
        delete_link = rule.delete_link + '/' + this.props.rstate + '/' + this.props.sortKey;
        time_link = rule.time_link + '/' + this.props.rstate + '/' + this.props.sortKey;
      } else if (this.props.rstate) {
        delete_link = rule.delete_link + '/' + this.props.rstate + '/source';
        time_link = rule.time_link + '/' + this.props.rstate + '/source';
      }

      var combutton = '';

      if (rule.comment) {
        combutton = React.createElement(TooltipButton, {
          text: rule.comment
        });
      }

      var trClass = Date.parse(rule.expires) < Date.now() ? 'warning' : '';
      return React.createElement("tr", {
        className: trClass
      }, React.createElement("td", null, rule.source), React.createElement("td", null, rule.source_port), React.createElement("td", null, rule.dest), React.createElement("td", null, rule.dest_port), React.createElement("td", null, rule.protocol), React.createElement("td", null, rule.expires), React.createElement("td", null, rule.action), React.createElement("td", null, rule.flags), React.createElement("td", null, rule.user), React.createElement("td", null, React.createElement(Button, {
        link: time_link,
        css: "primary",
        icon: "time"
      }), "\xA0", React.createElement(Button, {
        link: delete_link,
        css: "danger",
        icon: "remove"
      }), "\xA0", combutton));
    }
  }]);

  return RulesRow;
}(React.Component);

var RtbhRow =
/*#__PURE__*/
function (_React$Component4) {
  _inherits(RtbhRow, _React$Component4);

  function RtbhRow() {
    _classCallCheck(this, RtbhRow);

    return _possibleConstructorReturn(this, _getPrototypeOf(RtbhRow).apply(this, arguments));
  }

  _createClass(RtbhRow, [{
    key: "render",
    value: function render() {
      var rule = this.props.rule;
      var trClass = Date.parse(rule.expires) < Date.now() ? 'warning' : '';
      var delete_link = rule.delete_link + '/active/source';
      var time_link = rule.time_link + '/active/source';

      if (this.props.rstate && this.props.sortKey && this.props.filterText) {
        delete_link = rule.delete_link + '/' + this.props.rstate + '/' + this.props.sortKey + '/' + this.props.filterText;
        time_link = rule.time_link + '/' + this.props.rstate + '/' + this.props.sortKey + '/' + this.props.filterText;
      } else if (this.props.rstate && this.props.sortKey) {
        delete_link = rule.delete_link + '/' + this.props.rstate + '/' + this.props.sortKey;
        time_link = rule.time_link + '/' + this.props.rstate + '/' + this.props.sortKey;
      } else if (this.props.rstate) {
        delete_link = rule.delete_link + '/' + this.props.rstate + '/source';
        time_link = rule.time_link + '/' + this.props.rstate + '/source';
      }

      var combutton = '';

      if (rule.comment) {
        combutton = React.createElement(TooltipButton, {
          text: rule.comment
        });
      }

      return React.createElement("tr", {
        className: trClass
      }, React.createElement("td", null, rule.ipv4, " ", rule.ipv6), React.createElement("td", null, rule.community), React.createElement("td", null, rule.expires), React.createElement("td", null, rule.user), React.createElement("td", null, React.createElement(Button, {
        link: time_link,
        css: "primary",
        icon: "time"
      }), "\xA0", React.createElement(Button, {
        link: delete_link,
        css: "danger",
        icon: "remove"
      }), "\xA0", combutton));
    }
  }]);

  return RtbhRow;
}(React.Component);

var RulesTable =
/*#__PURE__*/
function (_React$Component5) {
  _inherits(RulesTable, _React$Component5);

  function RulesTable(props) {
    var _this;

    _classCallCheck(this, RulesTable);

    _this = _possibleConstructorReturn(this, _getPrototypeOf(RulesTable).call(this, props));

    _defineProperty(_assertThisInitialized(_this), "onSort", function (column) {
      return function (e) {
        var direction = _this.state.sort.column ? _this.state.sort.direction === 'asc' ? 'desc' : 'asc' : 'desc';
        var sort = {
          'column': column,
          'direction': direction
        };

        _this.props.onSortKeyChange(sort);

        _this.setState({
          sort: {
            column: column,
            direction: direction
          }
        });
      };
    });

    _defineProperty(_assertThisInitialized(_this), "setArrow", function (column) {
      var className = 'sort-direction';

      if (_this.state.sort.column === column) {
        className += _this.state.sort.direction === 'asc' ? ' asc' : ' desc';
      }

      return className;
    });

    _this.state = {
      sort: {
        column: null,
        direction: 'desc'
      }
    };
    return _this;
  }

  _createClass(RulesTable, [{
    key: "render",
    value: function render() {
      var cels = [];
      var columns = this.props.columns;

      for (var col in columns) {
        cels.push(React.createElement("th", {
          key: col,
          onClick: this.onSort(col)
        }, columns[col], React.createElement("span", {
          className: this.setArrow(col)
        })));
      }

      return React.createElement("table", {
        className: "table table-hover",
        id: this.props.cssId
      }, React.createElement("thead", null, React.createElement("tr", null, cels, React.createElement("th", null, "Action"))), React.createElement("tbody", null, this.props.rows));
    }
  }]);

  return RulesTable;
}(React.Component);

var TablesContainer =
/*#__PURE__*/
function (_React$Component6) {
  _inherits(TablesContainer, _React$Component6);

  function TablesContainer(props) {
    var _this2;

    _classCallCheck(this, TablesContainer);

    _this2 = _possibleConstructorReturn(this, _getPrototypeOf(TablesContainer).call(this, props));

    _defineProperty(_assertThisInitialized(_this2), "rulesColumns", {
      'source': 'Source address',
      'source_port': 'Source port',
      'dest': 'Dest. address',
      'dest_port': 'Dest. port',
      'protocol': 'Protocol',
      'expires': 'Expires',
      'action': 'Action',
      'flags': 'Flags',
      'user': 'User'
    });

    _defineProperty(_assertThisInitialized(_this2), "rtbhColumns", {
      'ipv4': 'IP adress (v4 or v6)',
      'community': 'Community',
      'expires': 'Expires',
      'user': 'User'
    });

    _this2.state = {
      sortKey: _this2.props.sortKey,
      sortDirection: 'asc',
      sortKeyRtbh: _this2.props.sortKey,
      sortDirectionRthb: 'asc'
    };
    _this2.handleSortKeyChange = _this2.handleSortKeyChange.bind(_assertThisInitialized(_this2));
    _this2.handleSortKeyRtbhChange = _this2.handleSortKeyRtbhChange.bind(_assertThisInitialized(_this2));
    return _this2;
  }

  _createClass(TablesContainer, [{
    key: "handleSortKeyChange",
    value: function handleSortKeyChange(sort) {
      this.setState({
        sortKey: sort['column'],
        sortDirection: sort['direction']
      });
    }
  }, {
    key: "handleSortKeyRtbhChange",
    value: function handleSortKeyRtbhChange(sort) {
      this.setState({
        sortKeyRtbh: sort['column'],
        sortDirectionRtbh: sort['direction']
      });
    }
  }, {
    key: "render",
    value: function render() {
      var _this3 = this;

      var filterText = this.props.filterText.toLowerCase();
      var rules_rows = [];
      var rtbh_rows = [];
      var column = Object.keys(this.rulesColumns).indexOf(this.state.sortKey) > -1 ? this.state.sortKey : 'source';
      var columnRtbh = Object.keys(this.rtbhColumns).indexOf(this.state.sortKeyRtbh) > -1 ? this.state.sortKeyRtbh : 'ipv4'; //filter out the rules
      // this.props.rtbh.filter((rule) => rule.fulltext.indexOf(filterText) > -1)

      var sortedRules = this.props.rules.filter(function (rule) {
        return rule.fulltext.indexOf(filterText) > -1;
      }).sort(function (a, b) {
        if (column === 'source' || column === 'dest') {
          return sortIp(a[column], b[column]);
        } else if (column === 'expires') {
          return sortExpires(a[column], b[column]);
        } else {
          return sortString(a[column], b[column]);
        }
      });
      var sortedRtbh = this.props.rtbh.filter(function (rule) {
        return rule.fulltext.indexOf(filterText) > -1;
      }).sort(function (a, b) {
        if (columnRtbh === 'ipv4') {
          return sortIp(a[columnRtbh], b[columnRtbh]);
        } else if (columnRtbh === 'expires') {
          return sortExpires(a[columnRtbh], b[columnRtbh]);
        } else {
          return sortString(a[(columnRtbh, b[columnRtbh])]);
        }
      });

      if (this.state.sortDirection === 'desc') {
        sortedRules = sortedRules.reverse();
      }

      if (this.state.sortDirectionRtbh === 'desc') {
        sortedRtbh = sortedRtbh.reverse();
      }

      sortedRules.forEach(function (rule) {
        rules_rows.push(React.createElement(RulesRow, {
          sortKey: _this3.state.sortKey,
          filterText: filterText,
          rstate: _this3.props.rstate,
          rule: rule,
          key: rule.fulltext
        }));
      });
      sortedRtbh.forEach(function (rule) {
        rtbh_rows.push(React.createElement(RtbhRow, {
          sortKey: _this3.state.sortKeyRtbh,
          filterText: filterText,
          rstate: _this3.props.rstate,
          rule: rule,
          key: rule.fulltext
        }));
      });
      return React.createElement("div", null, React.createElement("h2", null, this.props.title, " IPv4/IPv6 rules"), React.createElement(RulesTable, {
        cssId: "ip-table",
        columns: this.rulesColumns,
        rows: rules_rows,
        onSortKeyChange: this.handleSortKeyChange
      }), React.createElement("h2", null, this.props.title, " RTBH rules"), React.createElement(RulesTable, {
        cssId: "rtbh-table",
        columns: this.rtbhColumns,
        rows: rtbh_rows,
        onSortKeyChange: this.handleSortKeyRtbhChange
      }));
    }
  }]);

  return TablesContainer;
}(React.Component);

var SearchBar =
/*#__PURE__*/
function (_React$Component7) {
  _inherits(SearchBar, _React$Component7);

  function SearchBar(props) {
    var _this4;

    _classCallCheck(this, SearchBar);

    _this4 = _possibleConstructorReturn(this, _getPrototypeOf(SearchBar).call(this, props));
    _this4.handleFilterTextChange = _this4.handleFilterTextChange.bind(_assertThisInitialized(_this4));
    return _this4;
  }

  _createClass(SearchBar, [{
    key: "handleFilterTextChange",
    value: function handleFilterTextChange(e) {
      this.props.onFilterTextChange(e.target.value);
    }
  }, {
    key: "render",
    value: function render() {
      return React.createElement("form", {
        className: "navbar-form pull-right",
        role: "search"
      }, React.createElement("div", {
        className: "input-group"
      }, React.createElement("input", {
        className: "form-control",
        type: "text",
        placeholder: "Search...",
        value: this.props.filterText,
        onChange: this.handleFilterTextChange
      }), React.createElement("div", {
        className: "input-group-btn"
      }, React.createElement("button", {
        className: "btn btn-default"
      }, React.createElement("i", {
        className: "glyphicon glyphicon-search"
      })))));
    }
  }]);

  return SearchBar;
}(React.Component);

var FilterableTablesContainer =
/*#__PURE__*/
function (_React$Component8) {
  _inherits(FilterableTablesContainer, _React$Component8);

  function FilterableTablesContainer(props) {
    var _this5;

    _classCallCheck(this, FilterableTablesContainer);

    _this5 = _possibleConstructorReturn(this, _getPrototypeOf(FilterableTablesContainer).call(this, props));
    _this5.state = {
      filterText: _this5.props.filterStart
    };
    _this5.handleFilterTextChange = _this5.handleFilterTextChange.bind(_assertThisInitialized(_this5));
    return _this5;
  }

  _createClass(FilterableTablesContainer, [{
    key: "handleFilterTextChange",
    value: function handleFilterTextChange(filterText) {
      this.setState({
        filterText: filterText
      });
    }
  }, {
    key: "render",
    value: function render() {
      var cssActive = this.props.rstate === 'active' ? "active nav-item" : "nav-item";
      var cssExpired = this.props.rstate === 'expired' ? "active nav-item" : "nav-item";
      var cssAll = this.props.rstate === 'all' ? "active nav-item" : "nav-item";
      return React.createElement("div", {
        className: "row"
      }, React.createElement("div", {
        className: "container",
        id: "dashboard-nav"
      }, React.createElement("div", {
        className: "col-md-6"
      }, React.createElement("h1", null, "Default dashboard")), React.createElement("div", {
        className: "col-md-6"
      }, React.createElement("ul", {
        className: "nav nav-pills pull-right"
      }, React.createElement("li", null, React.createElement(SearchBar, {
        filterText: this.state.filterText,
        onFilterTextChange: this.handleFilterTextChange
      })), React.createElement("li", {
        className: cssActive
      }, React.createElement("a", {
        className: "nav-link",
        href: "/show/active/"
      }, "Active")), React.createElement("li", {
        className: cssExpired
      }, React.createElement("a", {
        className: "nav-link",
        href: "/show/expired/"
      }, "Expired")), React.createElement("li", {
        className: cssAll
      }, React.createElement("a", {
        className: "nav-link",
        href: "/show/all/"
      }, "All"))))), React.createElement(TablesContainer, {
        rules: this.props.rules,
        rtbh: this.props.rtbh,
        title: this.props.title,
        rstate: this.props.rstate,
        sortKey: this.props.sortKey,
        filterText: this.state.filterText
      }));
    }
  }]);

  return FilterableTablesContainer;
}(React.Component);

var domContainer = document.querySelector('#rules_table_container');
ReactDOM.render(React.createElement(FilterableTablesContainer, {
  rules: RULES,
  rtbh: RTBH,
  title: TITLE,
  filterStart: FILTER_START,
  rstate: RSTATE,
  sortKey: SORT_KEY
}), domContainer);