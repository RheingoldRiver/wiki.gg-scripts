from mwcleric import WikiggClient, AuthCredentials
from PIL import Image, UnidentifiedImageError
from mwclient.image import Image as mwclientImage
from requests import HTTPError


class Mover:
    local = 'temp.png'
    border_size = 2
    summary = "Cropping 2px border through an automated script. Please roll back if this image should be excluded."

    def __init__(self, from_site: WikiggClient, to_site: WikiggClient):
        self.from_site = from_site
        self.to_site = to_site

    def run(self):
        for file_page in self.from_site.client.allimages():
            file_page: mwclientImage
            with open(self.local, 'wb') as f:
                file_page.download(f)
            if not file_page.name.endswith('.png'):
                continue
            try:
                should_do_upload = self.process_image()
            except UnidentifiedImageError:
                continue
            if should_do_upload:
                try:
                    self.upload_image(file_page.page_title)
                except HTTPError:
                    continue
                    

    def has_transparent_border(self, image, width, height):
        # Check top and bottom borders
        for x in range(width):
            for y in range(self.border_size):  # Top border (y = 0 to 1) and bottom border (y = height - 2 to height - 1)
                if image.getpixel((x, y))[3] != 0 or image.getpixel((x, height - 1 - y))[3] != 0:
                    return False
        # Check left and right borders
        for y in range(height):
            for x in range(self.border_size):  # Left border (x = 0 to 1) and right border (x = width - 2 to width - 1)
                if image.getpixel((x, y))[3] != 0 or image.getpixel((width - 1 - x, y))[3] != 0:
                    return False
        return True

    def process_image(self):
        image = Image.open(self.local)

        # Ensure the image has an alpha (transparency) channel
        if image.mode != 'RGBA':
            image = image.convert('RGBA')

        # Get the size of the image
        width, height = image.size

        if not self.has_transparent_border(image, width, height):
            return False

        # Check for transparent border
        cropped_image = image.crop((2, 2, width - 2, height - 2))
        cropped_image.save(self.local)
        return True

    def upload_image(self, title):
        self.to_site.client.upload(file='temp.png', filename=title, comment=self.summary, ignore=True)


if __name__ == '__main__':
    credentials = AuthCredentials(user_file='me')
    source = WikiggClient('shogunshowdown', credentials=credentials)
    site1 = WikiggClient('shogunshowdown', credentials=credentials)
    Mover(source, site1).run()
