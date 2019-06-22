'use strict';

class Button extends React.Component {

    render() {
        const link = this.props.link;
        const css = "btn btn-" + this.props.css + " btn-sm";
        const icon = "glyphicon glyphicon-" + this.props.icon;

        return (
            <a className={css} href={link} role="button">
               <span className={icon}></span>
            </a>
        );

    }

}

class TooltipButton extends React.Component {

    render() {
        const text = this.props.text;

        return (
            <button type="button" className="btn btn-info btn-sm" data-toggle="tooltip" data-placement="top" title={text}>
                   <span className="glyphicon glyphicon-comment"></span>
            </button>
        )

    }
}


class RulesRow extends React.Component {


    render() {
        const rule = this.props.rule;
        const delete_link = rule.delete_link + '/' + this.props.rstate + '/' + this.props.sortKey + '/' + this.props.filterText;
        const time_link = rule.time_link + '/' + this.props.rstate + '/' + this.props.sortKey + '/' + this.props.filterText;

        let combutton = '';

        if (rule.comment) {
            combutton = <TooltipButton text={rule.comment} />;
        }

        return (
            <tr>
            <td>{rule.source}</td>
            <td>{rule.source_port}</td>
            <td>{rule.dest}</td>
            <td>{rule.dest_port}</td>
            <td>{rule.protocol}</td>
            <td>{rule.expires}</td>
            <td>{rule.action}</td>
            <td>{rule.flags}</td>
            <td>{rule.user}</td>
            <td>
                <Button link={time_link} css="primary" icon="time" />
                &nbsp;
                <Button link={delete_link} css="danger" icon="remove" />
                &nbsp;
                {combutton}
            </td>
          </tr>
        );
    }
}


class RtbhRow extends React.Component {


    render() {


        const rule = this.props.rule;
        const delete_link = rule.delete_link + '/' + this.props.rstate + '/' + this.props.sortKey + '/' + this.props.filterText;
        const time_link = rule.time_link + '/' + this.props.rstate + '/' + this.props.sortKey + '/' + this.props.filterText;
        let combutton = '';


        if (rule.comment) {
            combutton = <TooltipButton text={rule.comment} />;
        }

        return (
            <tr>
            <td>{rule.ipv4} {rule.ipv6}</td>
            <td>{rule.community}</td>
            <td>{rule.expires}</td>
            <td>{rule.user}</td>
            <td>
                <Button link={time_link} css="primary" icon="time" />
                &nbsp;
                <Button link={delete_link} css="danger" icon="remove" />
                &nbsp;
                {combutton}
            </td>
          </tr>
        );
    }
}



class RulesTable extends React.Component {

    constructor(props) {
        super(props);
        this.state = {
            sort: {
                column: null,
                direction: 'desc',
            }
        };
    }


    onSort = (column) => (e) => {
        const direction = this.state.sort.column ? (this.state.sort.direction === 'asc' ? 'desc' : 'asc') : 'desc';

        const sort = {
            'column': column,
            'direction': direction
        };

        this.props.onSortKeyChange(sort);

        this.setState({
            sort: {
                column,
                direction,
            }
        });

    };

    setArrow = (column) => {
        let className = 'sort-direction';

        if (this.state.sort.column === column) {
            className += this.state.sort.direction === 'asc' ? ' asc' : ' desc';
        }

        return className;
    };



    render() {

        let cels = [];

        const columns = this.props.columns;

        for (let col in columns) {
            cels.push(<th key={col} onClick={this.onSort(col)}>
                              {columns[col]}
                              <span className={this.setArrow(col)}></span>
                              </th>)
        }


        return (
            <table className="table table-hover" id={this.props.cssId}>
                 <thead>
                    <tr>
                    {cels}
                    <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>{this.props.rows}</tbody>
                </table>
        );

    }
}


class TablesContainer extends React.Component {

    constructor(props) {
        super(props);
        this.state = {
            sortKey: this.props.sortKey,
            sortDirection: 'asc',
            sortKeyRtbh: this.props.sortKey,
            sortDirectionRthb: 'asc'
        };

        this.handleSortKeyChange = this.handleSortKeyChange.bind(this);
        this.handleSortKeyRtbhChange = this.handleSortKeyRtbhChange.bind(this);

    }

    handleSortKeyChange(sort) {
        this.setState({
            sortKey: sort['column'],
            sortDirection: sort['direction']
        });
    }

    handleSortKeyRtbhChange(sort) {
        this.setState({
            sortKeyRtbh: sort['column'],
            sortDirectionRtbh: sort['direction']
        });
    }

    rulesColumns = {
            'source': 'Source address',
            'source_port': 'Source port',
            'dest': 'Dest. address',
            'dest_port': 'Dest. port',
            'protocol': 'Protocol',
            'expires': 'Expires',
            'action': 'Action',
            'flags': 'Flags',
            'user': 'User'
    };

    rtbhColumns = {
            'ipv4': 'IP adress (v4 or v6)',
            'community': 'Community',
            'expires': 'Expires',
            'user': 'User'
    };


    render() {
        const filterText = this.props.filterText.toLowerCase();
        const rules_rows = [];
        const rtbh_rows = [];
        const column = Object.keys(this.rulesColumns).indexOf(this.state.sortKey) > -1 ? this.state.sortKey : 'source';
        const columnRtbh = Object.keys(this.rtbhColumns).indexOf(this.state.sortKeyRtbh) > -1 ? this.state.sortKeyRtbh : 'ipv4';



        //filter out the rules
        // this.props.rtbh.filter((rule) => rule.fulltext.indexOf(filterText) > -1)

        let sortedRules = this.props.rules.filter((rule) => rule.fulltext.indexOf(filterText) > -1).sort((a, b) => {
            const nameA = a[column].toLowerCase(); // ignore upper and lowercase
            const nameB = b[column].toLowerCase(); // ignore upper and lowercase

            if (nameA < nameB) {
                return -1;
            }
            if (nameA > nameB) {
                return 1;
            }

            // names must be equal
            return 0;

        });

        let sortedRtbh = this.props.rtbh.filter((rule) => rule.fulltext.indexOf(filterText) > -1).sort((a, b) => {
            const nameA = a[columnRtbh].toLowerCase(); // ignore upper and lowercase
            const nameB = b[columnRtbh].toLowerCase(); // ignore upper and lowercase

            if (nameA < nameB) {
                return -1;
            }
            if (nameA > nameB) {
                return 1;
            }

            // names must be equal
            return 0;

        });

        if (this.state.sortDirection === 'desc') {
            sortedRules = sortedRules.reverse();
        }

        if (this.state.sortDirectionRtbh === 'desc') {
            sortedRtbh = sortedRtbh.reverse();
        }

        sortedRules.forEach((rule) => {
            rules_rows.push(
                <RulesRow
                  sortKey={this.state.sortKey}
                  filterText={filterText}
                  rstate={this.props.rstate}
                  rule={rule}
                  key={rule.fulltext}
                />
            );
        });

        sortedRtbh.forEach((rule) => {
            rtbh_rows.push(
                <RtbhRow
                  sortKey={this.state.sortKeyRtbh}
                  filterText={filterText}
                  rstate={this.props.rstate}
                  rule={rule}
                  key={rule.fulltext}
                />
            );
        });

        return (
            <div>
                <h2>{this.props.title} IPv4/IPv6 rules</h2>
                <RulesTable
                    cssId='ip-table'
                    columns={this.rulesColumns}
                    rows={rules_rows}
                    onSortKeyChange={this.handleSortKeyChange}
                    />
                <h2>{this.props.title} RTBH rules</h2>
                <RulesTable
                    cssId='rtbh-table'
                    columns={this.rtbhColumns}
                    rows={rtbh_rows}
                    onSortKeyChange={this.handleSortKeyRtbhChange}
                    />
            </div>
        );
    }
}




class SearchBar extends React.Component {
    constructor(props) {
        super(props);
        this.handleFilterTextChange = this.handleFilterTextChange.bind(this);
    }

    handleFilterTextChange(e) {
        this.props.onFilterTextChange(e.target.value);
    }

    render() {
        return (

            <form className="navbar-form pull-right" role="search">
                <div className="input-group">
                    <input
                        className="form-control"
                        type="text"
                        placeholder="Search..."
                        value={this.props.filterText}
                        onChange={this.handleFilterTextChange}
                    />
                    <div className="input-group-btn">
                        <button className="btn btn-default"><i className="glyphicon glyphicon-search"></i></button>
                    </div>
                </div>
            </form>
        );
    }
}

class FilterableTablesContainer extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            filterText: this.props.filterStart
        };

        this.handleFilterTextChange = this.handleFilterTextChange.bind(this);
    }

    handleFilterTextChange(filterText) {
        this.setState({
            filterText: filterText
        });
    }

    render() {

        const cssActive = this.props.rstate === 'active' ? "active nav-item" : "nav-item";
        const cssExpired = this.props.rstate === 'expired' ? "active nav-item" : "nav-item";
        const cssAll = this.props.rstate === 'all' ? "active nav-item" : "nav-item";

        return (
         <div className="row">
             <div className="container" id="dashboard-nav">
                 <div className="col-md-6">
                     <h1>Default dashboard</h1>
                 </div>
                 <div className="col-md-6">
                     <ul className="nav nav-pills pull-right">
                         <li>
                             <SearchBar
                        filterText={this.state.filterText}
                        onFilterTextChange={this.handleFilterTextChange}
                      />
                         </li>
                         <li className={cssActive}>
                             <a className="nav-link" href="/show/active/">Active</a>
                         </li>
                         <li className={cssExpired}>
                             <a className="nav-link"
                                href="/show/expired/">Expired</a>
                         </li>
                         <li className={cssAll}>
                             <a className="nav-link" href="/show/all/">All</a>
                         </li>
                     </ul>
                 </div>
             </div>

              <TablesContainer
                rules={this.props.rules}
                rtbh={this.props.rtbh}
                title={this.props.title}
                rstate={this.props.rstate}
                sortKey={this.props.sortKey}
                filterText={this.state.filterText}
              />
        </div>
        );
    }
}



const domContainer = document.querySelector('#rules_table_container');
ReactDOM.render(<FilterableTablesContainer rules={RULES} rtbh={RTBH} title={TITLE} filterStart={FILTER_START}  rstate={RSTATE} sortKey={SORT_KEY}/>, domContainer);