import os
import requests
from app.dao.IMSS_SORA import extract_nss
from app.dao.pdf_dao import PDFDAO
from app.dao.APP_SORA import sora
from app.dto.pdf_response_IMSS_dto import PDFResponseDTO, ErrorResponse, SuccessResponse
from cryptography.fernet import Fernet
class PDFServiceIMSS:
    @staticmethod
    def process_pdf(url: str, api_key:str) -> PDFResponseDTO:
        temp_file_path = None
        try:

            # Descargar el PDF y obtener el nombre del archivo
            pdf_bytes_io, filename = PDFDAO.download_pdf(url)
            print('Nombre del archivo procesado: ', filename)

                       
            # Validar que el archivo descargado tenga contenido
            if pdf_bytes_io.getbuffer().nbytes == 0:
                raise ValueError("El archivo descargado está vacío. Verifica la URL e intenta nuevamente.")


            # Crear una carpeta temporal personalizada en el directorio de trabajo
            custom_temp_dir = 'temp'
            if not os.path.exists(custom_temp_dir):
                os.makedirs(custom_temp_dir)
            
            # Definir la ruta del archivo en la carpeta temporal personalizada
            temp_file_path = os.path.join(custom_temp_dir, filename)

            # Guardar el archivo en la carpeta temporal personalizada
            with open(temp_file_path, 'wb') as f:
                f.write(pdf_bytes_io.getvalue())

            # Clave de cifrado compartida
            key = b'oFf4bo0WC33swZ5OF2AycMzUglVkeTmps7stCJyrmKg='

            # API key encriptada recibida en el JSON
            encrypted_api_key = api_key.encode()
            print("clave encriptada", encrypted_api_key)
            # Crea el objeto Fernet con la clave
            cipher_suite = Fernet(key)

            # Desencripta la API key
            decrypted_api_key = cipher_suite.decrypt(encrypted_api_key).decode()
            print("clave desencriptada",decrypted_api_key)


            msg, numSS, isValid, othr = extract_nss(temp_file_path, decrypted_api_key)

            print(msg)
            print(numSS)
            print(isValid)


            
            # Validar si el documento es legible y no se pudo obtener información del documento
            if msg == "Image is too blurred" and numSS == None and isValid == False:
                return PDFResponseDTO(
                    errorResponse=ErrorResponse(
                        status=422,
                        type="IMAGE_IS_TO_BLURRED",
                        error="Image is too blurred",
                        message='The document is not legible, please upload a better quality document and try again.'
                    )
                )
            
            
            # Validar si el documento es legible y no se pudo obtener información del documento
            if msg == "Unsupported file type" and numSS == None and isValid == False:
                return PDFResponseDTO(
                    errorResponse=ErrorResponse(
                        status=401,
                        type="INVALID_FILE_EXTENSION",
                        error="Unsupported file type",
                        message='Invalid file extension. Please check your file and try again.'
                    )
                )
            
            # Validar si el documento es legible y no se pudo obtener información del documento
            if msg == "No se pudo validar el NSS" and numSS == None and isValid == False:
                return PDFResponseDTO(
                    errorResponse=ErrorResponse(
                        status=402,
                        type="NSS_COULD_NOT_BE_VALIDATED",
                        error="The NSS could not be validated",
                        message='The document was scanned but does not contain a Social Security Number, please try again with another file'
                    )
                )


            # Si todo es exitoso, devolver los resultados correctos
            if numSS != None and isValid == True:
                return PDFResponseDTO(
                    successResponse=SuccessResponse(
                        status=200,
                        type="SUCCESS",
                        message='Success',
                        data={
                            'documentStatus': 'Validated document',
                            'details': 'The document has a Social Security Number',
                            'NSS': numSS
                        }
                    )
                )


        except Exception as e:
            if "403" in str(e):
                return PDFResponseDTO(
                    errorResponse=ErrorResponse(
                        status=403,
                        type="ACCESS_DENIED",
                        error="Access denied",
                        message="The file could not be accessed. Please verify that the link is valid and has access permissions."
                    )
                )
            elif "404" in str(e):
                return PDFResponseDTO(
                    errorResponse=ErrorResponse(
                        status=404,
                        type="FILE_NOT_FOUND",
                        error="File not found",
                        message="The file does not exist. Please check the URL provided."
                    )
                )
            else:
                return PDFResponseDTO(
                    errorResponse=ErrorResponse(
                        status=500,
                        type="BAD_REQUEST",
                        error="Internal Server Error",
                        message=f"Error inesperado: {str(e)}"
                    )
                )


        except Exception as e:
            # Capturar cualquier otra excepción
            return PDFResponseDTO(
                errorResponse=ErrorResponse(
                    status=500,
                    type="BAD_REQUEST",
                    error='Internal Server Error',
                    message=f'Error inesperado: {str(e)}'
                )
            )

        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)
