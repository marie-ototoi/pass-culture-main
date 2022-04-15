import React from 'react'
import {
  ReferenceInput,
  AutocompleteInput,
  Create,
  SimpleForm,
  TextInput,
  NumberInput,
  SelectInput,
} from 'react-admin'

export const DECIMAL_STEP = .00001

export function SignalCreate(props = {}) {
  return (
    <Create {...props}>
      <SimpleForm>
        <ReferenceInput
          // label="Binance symbol"
          source="baseAsset"
          reference="binance/api/v1/exchangeInfo"
        >
          <AutocompleteInput
            optionText="baseAsset"
            // source="pair1"
            // choices={[
            //   { id: 'BTC', name: 'BTC' },
            //   { id: 'ETH', name: 'ETH' },
            //   { id: 'EGLD', name: 'EGLD' },
            //   { id: 'LUNA', name: 'LUNA' },
            //   { id: 'LTC', name: 'LTC' },
            // ]}
          />
        </ReferenceInput>
        <TextInput source="pair2" defaultValue="USDT" disabled />
        <SelectInput
          source="direction"
          choices={[
            { id: 1, name: 'LONG' },
            { id: 2, name: 'SHORT', disabled: true },
          ]}
        />
        <NumberInput source="zoneStart" step={DECIMAL_STEP} />
        <NumberInput source="zoneEnd" step={DECIMAL_STEP} />
        <SelectInput
          source="orderTypes"
          choices={[
            { id: 1, name: 'LIMIT' },
            { id: 2, name: 'MARKET', disabled: true },
          ]}
        />
        <NumberInput source="limiteOrderPrice" step={DECIMAL_STEP} />
        <NumberInput source="stopLossPrice" step={DECIMAL_STEP}  />
        <NumberInput source="takeProfitPriceOne" />
        <NumberInput source="takeProfitPriceTwo" />
        <NumberInput source="takeProfitPriceThree" />
        <SelectInput
          source="status"
          choices={[
            { id: 1, name: 'PENDING' },
            { id: 2, name: 'DONE' },
            { id: 3, name: 'IN_PROGRESS' },
            { id: 4, name: 'CANCELED' },
            { id: 5, name: 'REPLACED' },
          ]}
        />
        <TextInput source="comment" />
      </SimpleForm>
    </Create>
  )
}
