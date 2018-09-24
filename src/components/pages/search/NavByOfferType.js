import PropTypes from 'prop-types'
import React from 'react'
import { connect } from 'react-redux'

import selectTypeSublabels from '../../../selectors/selectTypeSublabels'

const NavByOfferType = ({ handleQueryParamsChange, title, typeSublabels }) => (
  <div>
    <h2>
      {title}
    </h2>
    {typeSublabels.map(typeSublabel => (
      <div className="field checkbox" key={typeSublabel} id="search-type-card">
        <input
          id="search-type-checkbox"
          className="input is-normal"
          onChange={() =>
            handleQueryParamsChange(
              { categories: typeSublabel },
              { pathname: '/recherche/resultats' }
            )
          }
          type="checkbox"
        />
        <label
          className="label"
          id="search-type-label"
          htmlFor="search-type-checkbox"
        >
          {' '}
          {typeSublabel}
        </label>
      </div>
    ))}
  </div>
)

NavByOfferType.propTypes = {
  handleQueryParamsChange: PropTypes.func.isRequired,
  title: PropTypes.string.isRequired,
  typeSublabels: PropTypes.array.isRequired,
}

export default connect(state => ({
  typeSublabels: selectTypeSublabels(state),
}))(NavByOfferType)
