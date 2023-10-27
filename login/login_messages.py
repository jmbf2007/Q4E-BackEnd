USER_ALREADY_CREATED = """
    <html>
    <head>
        <title>Usuario ya creado</title>
        <style>
            body {
                text-align: center;
                padding-top: 5em;
                font-family: Arial, sans-serif;
            }
            hr {
                margin: 2em auto;
                width: 50%;
            }
        </style>
    </head>
    <body>
        <h2>Usuario ya creado</h2>
        <hr>
        <p>El correo habia sido verificado</p>
        <p>No es necesario nueva verificacion</p>
        <hr>
        <p>Quant4Everybody</p>
    </body>
    </html>
    """  

VERIFICATION_FAILED = """
    <html>
    <head>
        <title>Verificación fallida</title>
        <style>
            body {
                text-align: center;
                padding-top: 5em;
                font-family: Arial, sans-serif;
            }
            hr {
                margin: 2em auto;
                width: 50%;
            }
        </style>
    </head>
    <body>
        <h2>Verificación Fallida</h2>
        <hr>
        <p>Error al verificar sus datos</p>
        <p>Usuario no creado</p>
        <hr>
        <p>Quant4Everybody</p>
    </body>
    </html>
    """    

VERIFICATION_SUCCESSFUL = """
    <html>
        <head>
            <title>Verificación exitosa</title>
            <style>
                body {
                    text-align: center;
                    padding-top: 5em;
                    font-family: Arial, sans-serif;
                }
                hr {
                    margin: 2em auto;
                    width: 50%;
                }
            </style>
        </head>
        <body>
            <h2>Verificación Exitosa</h2>
            <hr>
            <p>¡Gracias por verificar tu correo electrónico!</p>
            <p>Tu cuenta ha sido creada.</p>
            <hr>
            <p>Quant4Everybody</p>
        </body>
    </html>
    """

EXPIRED_TOKEN = """
    <html>
    <head>
        <title>Verificación fallida</title>
        <style>
            body {
                text-align: center;
                padding-top: 5em;
                font-family: Arial, sans-serif;
            }
            hr {
                margin: 2em auto;
                width: 50%;
            }
        </style>
    </head>
    <body>
        <h2>Verificación Fallida</h2>
        <hr>
        <p>El token ha expirado</p>
        <p>Usuario no creado</p>
        <hr>
        <p>Quant4Everybody</p>
    </body>
    </html>
    """

INVALID_TOKEN = """
    <html>
    <head>
        <title>Verificación fallida</title>
        <style>
            body {
                text-align: center;
                padding-top: 5em;
                font-family: Arial, sans-serif;
            }
            hr {
                margin: 2em auto;
                width: 50%;
            }
        </style>
    </head>
    <body>
        <h2>Verificación Fallida</h2>
        <hr>
        <p>El token no es válido</p>
        <p>Usuario no creado</p>
        <hr>
        <p>Quant4Everybody</p>
    </body>
    </html>
    """

RECOVERY_PASSWORD_SUCCESSFUL = """
    <html>
        <head>
            <title>Password Actualizado</title>
            <style>
                body {
                    text-align: center;
                    padding-top: 5em;
                    font-family: Arial, sans-serif;
                }
                hr {
                    margin: 2em auto;
                    width: 50%;
                }
            </style>
        </head>
        <body>
            <h2>Password Actualizado</h2>
            <hr>
            <p>El password ha sido actualizado correctamente</p>
            <p>Ingrese en la cuenta</p>
            <hr>
            <p>Quant4Everybody</p>
        </body>
    </html>
    """