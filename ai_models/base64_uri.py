import base64
import mimetypes


def path2base64URI(file_path):
    mime_type, _ = mimetypes.guess_type(file_path)
    with open(file_path, "rb") as image_file:
        base64_data = base64.b64encode(image_file.read()).decode("utf-8")
    data_uri = f"data:{mime_type};base64,{base64_data}"
    # print(data_uri)
    return data_uri

# path2base64URI("/Users/andrew/Documents/images/img2.png")