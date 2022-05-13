import {useState} from "react";
import {Grid} from "@mui/material";
import {DateField, RichTextField, Show, SimpleShowLayout, TextField} from "react-admin";

const UserDetail = () => {
    return (<Show>
        <SimpleShowLayout>
            <TextField source="id"/>
            <TextField source="firstName"/>
            <TextField source="lastName"/>
            <TextField source="email"/>
            <TextField source="phoneNumber"/>
        </SimpleShowLayout>
    </Show>)

};

export default UserDetail;