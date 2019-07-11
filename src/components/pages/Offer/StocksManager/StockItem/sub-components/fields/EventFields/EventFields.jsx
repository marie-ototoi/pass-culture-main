import moment from 'moment'
import PropTypes from 'prop-types'
import React, { PureComponent, Fragment } from 'react'

import {
  DateField,
  HiddenField,
  TimeField,
} from 'components/layout/form/fields'

export class EventFields extends PureComponent {
  render() {
    const { beginningMinDate, readOnly, stocks, timezone } = this.props
    const highlightDates = (stocks || []).map(stock => stock.beginningDatetime)

    return (
      <Fragment>
        <td>
          <DateField
            highlightDates={highlightDates}
            minDate={beginningMinDate || moment()}
            name="beginningDatetime"
            readOnly={readOnly}
            required
            timezone={timezone}
            title="Date"
          />
        </td>
        <td>
          <TimeField
            name="beginningTime"
            patchKey="beginningDatetime"
            readOnly={readOnly}
            required
            title="Heure"
          />
        </td>
        <td>
          <HiddenField name="endDatetime" />
          <TimeField
            name="endTime"
            patchKey="endDatetime"
            readOnly={readOnly}
            required
            title="Heure de fin"
          />
        </td>
      </Fragment>
    )
  }
}

EventFields.defaultProps = {
  beginningMinDate: null,
  readOnly: true,
  stocks: null,
  timezone: null,
}

EventFields.propTypes = {
  beginningMinDate: PropTypes.string,
  dispatch: PropTypes.func.isRequired,
  readOnly: PropTypes.bool,
  stocks: PropTypes.arrayOf,
  timezone: PropTypes.string,
}

export default EventFields
