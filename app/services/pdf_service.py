import os
from app.dao.pdf_dao import PDFDAO
from app.dao.APP_SORA import sora
from app.dto.pdf_response_dto import PDFResponseDTO, ErrorResponse, MismatchResponse, OCROnlyResponse, SuccessResponse
from cryptography.fernet import Fernet

class PDFService:
    @staticmethod
    def process_pdf(url: str, api_key:str) -> PDFResponseDTO:
        temp_file_path = None
        try:
            # Descargar el PDF y obtener el nombre del archivo
            pdf_bytes_io, filename = PDFDAO.download_pdf(url)
            print('Nombre del archivo procesado: ', filename)

                       
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


            # Llamar a la función sora con la ruta del archivo temporal
            check, sat, document = sora(temp_file_path, decrypted_api_key)
            
            print(check)
            print(sat)
            print(document)


            # Validar si el documento es legible y no se pudo obtener información del documento
            if check == "Image is too blurred" and sat == None and document == None:
                return PDFResponseDTO(
                    errorResponse=ErrorResponse(
                        status=422,
                        type="IMAGE_IS_TO_BLURRED",
                        error="Image is too blurred",
                        message='The document is not legible, please upload a better quality document and try again.'
                    )
                )

            # Validar el mismatch (cuando la información del documento no coincide con la del SAT)
            if check == "SAT<>DOC":
                return PDFResponseDTO(
                    mismatchResponse=MismatchResponse(
                        status=202,
                        type="MISMATCH",
                        message='Mismatch',
                        data={
                            'documentStatus': 'The document does not match the SAT',
                            'details': 'The information extracted from the document and from the SAT do not match in one or more fields',
                            'webScrapingData': sat,
                            'documentData': document
                        }
                    )
                )
            
            if check == 'QR code not detected' and sat == None and document == None:
                return PDFResponseDTO(
                    errorResponse=ErrorResponse(
                        status=409,
                        type="CONFLICT",
                        error='Conflict',
                        message='The document does not match the reference values, please upload a document that meets the values ​​and try again.'
                    )
                )

            # Si el scraping del SAT no es exitoso, pero el OCR es válido
            if check == 'SAT no accesible' and sat == None:
                return PDFResponseDTO(
                    ocrOnlyResponse=OCROnlyResponse(
                        status=201,
                        type="OCR_ONLY",
                        message='OCR Only',
                        data={
                            'documentStatus': 'Validated without SAT service',
                            'details': 'The scraping service has failed or is unavailable. Validation performed with OCR',
                            'documentData': document
                        }
                    )
                )

            # Si todo es exitoso, devolver los resultados correctos
            return PDFResponseDTO(
                successResponse=SuccessResponse(
                    status=200,
                    type="SUCCESS",
                    message='Success',
                    data={
                        'documentStatus': 'Validated document',
                        'details': 'Successful validation, the CIF and RFC match in the document and on the SAT page.',
                        'webScrapingData': sat,
                        'documentData': document
                    }
                )
            )

        except ValueError as ve:
        # Capturar errores de valor específico
            return PDFResponseDTO(
                errorResponse=ErrorResponse(
                    status=400,
                    type="BAD_REQUEST",
                    error='Bad request',
                    message=str(ve)
                )
            )
        
        except UnboundLocalError as ule:
            # Capturar específicamente el UnboundLocalError
            return PDFResponseDTO(
                errorResponse=ErrorResponse(
                    status=400,
                    type="BAD_REQUEST",
                    error='Bad request',
                    message='Invalid file extension. Please check your file and try again.'
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