# Important imports
from app import app
from flask import request, render_template, send_from_directory, url_for
import os
from skimage.metrics import structural_similarity
import imutils
import cv2
from PIL import Image

# Adding path to config
app.config['INITIAL_FILE_UPLOADS'] = 'app/static/uploads'
app.config['EXISTNG_FILE'] = 'app/static/original'
app.config['GENERATED_FILE'] = 'app/static/generated'


# Route to display the uploaded image
@app.route('/static/uploads/<filename>')
def send_uploaded_file(filename):
    return send_from_directory(app.config['INITIAL_FILE_UPLOADS'], filename)

# Function to determine tampering threshold based on sensitivity
def get_threshold(sensitivity):
    if sensitivity == "high":
        return 0.9
    elif sensitivity == "medium":
        return 0.8
    else:
        return 0.7  # Low sensitivity, allowing more differences

# Route to home page
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return render_template("index.html", pred=None, uploaded_img=None)

    if request.method == "POST":
        # Get uploaded image
        file_upload = request.files['file_upload']
        filename = file_upload.filename

        # Resize and save the uploaded image
        uploaded_image = Image.open(file_upload).resize((250, 160))
        uploaded_image = uploaded_image.convert("RGB")
        uploaded_image_path = os.path.join(app.config['INITIAL_FILE_UPLOADS'], 'image.jpg')
        uploaded_image.save(uploaded_image_path)

        # Resize and save the original image to ensure both uploaded and original matches in size
        original_image = Image.open(os.path.join(app.config['EXISTNG_FILE'], 'image.jpg')).resize((250, 160))
        original_image.save(os.path.join(app.config['EXISTNG_FILE'], 'image.jpg'))

        # Read uploaded and original image as array
        original_image = cv2.imread(os.path.join(app.config['EXISTNG_FILE'], 'image.jpg'))
        uploaded_image = cv2.imread(uploaded_image_path)

        # Convert images to grayscale
        original_gray = cv2.cvtColor(original_image, cv2.COLOR_BGR2GRAY)
        uploaded_gray = cv2.cvtColor(uploaded_image, cv2.COLOR_BGR2GRAY)

        # Calculate structural similarity
        (score, diff) = structural_similarity(original_gray, uploaded_gray, full=True)
        diff = (diff * 255).astype("uint8")

        # Calculate threshold and contours
        thresh = cv2.threshold(diff, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
        cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)

        # Draw contours on images
        for c in cnts:
            (x, y, w, h) = cv2.boundingRect(c)
            cv2.rectangle(original_image, (x, y), (x + w, y + h), (0, 0, 255), 2)
            cv2.rectangle(uploaded_image, (x, y), (x + w, y + h), (0, 0, 255), 2)

        # Save all output images
        cv2.imwrite(os.path.join(app.config['GENERATED_FILE'], 'image_original.jpg'), original_image)
        cv2.imwrite(os.path.join(app.config['GENERATED_FILE'], 'image_uploaded.jpg'), uploaded_image)
        cv2.imwrite(os.path.join(app.config['GENERATED_FILE'], 'image_diff.jpg'), diff)
        cv2.imwrite(os.path.join(app.config['GENERATED_FILE'], 'image_thresh.jpg'), thresh)

        # Get tampering threshold based on desired sensitivity
        sensitivity = "medium"  # Can be high, medium, or low
        tampering_threshold = get_threshold(sensitivity)

        # Determine if the image is tampered or original based on the score
        if score < tampering_threshold:
            message = "The image is tampered!"
        else:
            message = "The image is original!"

        # Pass the uploaded image path to the template
        return render_template(
            'index.html',
            pred=f"{round(score*100, 2)}% similarity - {message}",
            # uploaded_img=url_for('send_uploaded_file', filename='image_uploaded.jpg')  # Pass the image path for display
        )


# Main function
if __name__ == '__main__':
    app.run(debug=True)
