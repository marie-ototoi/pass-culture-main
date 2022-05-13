import React, {useState, useEffect} from 'react';
import {useLogin as userLogin} from 'react-admin';
import {Button, CardActions, CircularProgress} from '@mui/material';

const LoginForm = () => {
    const [loading, setLoading] = useState(false);
    const login = userLogin();
    useEffect(() => {
        const {searchParams} = new URL(window.location.href);
        const code = searchParams.get('code');
        const state = searchParams.get('state');

        // If code is present, we came back from the provider
        if (code && state) {
            setLoading(true);
            login({code, state});
        }
    }, [login])
    const handleLogin = () => {
        setLoading(true);
        login({});
    };

    return (
        <div>
            <CardActions>
                <Button
                    variant="contained"
                    type="submit"
                    color="primary"
                    onClick={handleLogin}
                    disabled={loading}
                >
                    {loading && (
                        <CircularProgress
                            size={18}
                            thickness={2}
                        />
                    )}
                    Login With Google
                </Button>
            </CardActions>
        </div>
    );
}

export default LoginForm;