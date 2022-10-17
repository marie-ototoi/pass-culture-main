import { StockCreationBodyModel, StockEditionBodyModel } from 'apiClient/v1'
import {
  IStockThingFormValues,
  STOCK_THING_FORM_DEFAULT_VALUES,
} from 'new_components/StockThingForm'

import { serializeStockThingList } from '../serializers'

describe('screens::StockThing::serializers:serializeStockThingList', () => {
  let formValues: IStockThingFormValues
  let departementCode: string

  beforeEach(() => {
    formValues = {
      remainingQuantity: STOCK_THING_FORM_DEFAULT_VALUES.remainingQuantity,
      bookingsQuantity: STOCK_THING_FORM_DEFAULT_VALUES.bookingsQuantity,
      quantity: '12',
      bookingLimitDatetime: new Date('2022-10-26T23:00:00+0200'),
      price: '10',
    }
    departementCode = '75'
  })

  it('should serialize data for stock thing creation', async () => {
    const expectedApiStockThing: StockCreationBodyModel = {
      bookingLimitDatetime: '2022-10-26T21:59:59Z',
      price: 10,
      quantity: 12,
    }

    const serializedData = serializeStockThingList(formValues, departementCode)
    expect(serializedData).toStrictEqual([expectedApiStockThing])
  })

  it('should serialize data for stock thing without "bookingLimitDatetime"', async () => {
    const expectedApiStockThing: StockCreationBodyModel = {
      bookingLimitDatetime: null,
      price: 10,
      quantity: 12,
    }

    const serializedData = serializeStockThingList(
      {
        ...formValues,
        bookingLimitDatetime: null,
      },
      departementCode
    )
    expect(serializedData).toStrictEqual([expectedApiStockThing])
  })

  it('should serialize data for stock thing edition', async () => {
    const expectedApiStockThing: StockEditionBodyModel = {
      humanizedId: 'STOCK_ID',
      bookingLimitDatetime: '2022-10-26T21:59:59Z',
      price: 10,
      quantity: 12,
    }

    const serializedData = serializeStockThingList(
      {
        stockId: 'STOCK_ID',
        ...formValues,
      },
      departementCode
    )
    expect(serializedData).toStrictEqual([expectedApiStockThing])
  })
})
