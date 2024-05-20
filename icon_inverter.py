from PIL import Image, ImageChops, ImageOps
import os

def process_images(folder_path):
    """Processes PNG images, creating black/white versions with transparency."""

    for filename in os.listdir(folder_path):
        if filename.endswith(".png"):
            img_path = os.path.join(folder_path, filename)

            try:
                with Image.open(img_path).convert("RGBA") as img:
                    # Create "_dark" version (black where not transparent)
                    dark_img = img.convert("L")  # Convert to grayscale
                    dark_img = ImageOps.colorize(dark_img, black=(0, 0, 0), white=(0, 0, 0))  # Black only
                    dark_img.putalpha(img.split()[-1])  # Restore original alpha
                    dark_name = os.path.splitext(filename)[0] + "_light.png"
                    dark_img.save(os.path.join(folder_path, dark_name))

                    # Create "_light" version (white where not transparent)
                    light_img = img.convert("L")  # Convert to grayscale
                    light_img = ImageOps.colorize(light_img, black=(255, 255, 255), white=(255, 255, 255))  # White only
                    light_img.putalpha(img.split()[-1])  # Restore original alpha
                    light_name = os.path.splitext(filename)[0] + "_dark.png"
                    light_img.save(os.path.join(folder_path, light_name))
            except Exception as e:
                print(f"Error processing {filename}: {e}")


if __name__ == "__main__":
    folder_path = input("Enter the path to the folder containing PNG images: ")
    process_images(folder_path)
    print("Image processing complete!")
