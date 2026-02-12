Based on the Postiz API documentation and schema, here is the specific syntax to programmatically upload a TikTok carousel.

### 1. The Concept

Postiz handles TikTok carousels (Photo Mode) by accepting an **array of images** within the `value` object. You do not need a specific "carousel" flag; if you provide multiple images to a TikTok integration ID, Postiz interprets it as a carousel.

### 2. The Syntax (cURL)

**Endpoint:** `POST /api/public/v1/posts`

```bash
curl -X POST "https://api.postiz.com/public/v1/posts" \
  -H "Authorization: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
  "type": "now",
  "posts": [
    {
      "integration": {
        "id": "YOUR_TIKTOK_INTEGRATION_ID"
      },
      "value": [
        {
          "content": "This is my automated carousel caption! #tiktok #automation",
          "image": [
            {
              "path": "https://your-public-server.com/slide1.jpg"
            },
            {
              "path": "https://your-public-server.com/slide2.jpg"
            },
            {
              "path": "https://your-public-server.com/slide3.jpg"
            }
          ]
        }
      ]
    }
  ]
}'

```

### 3. Critical Requirements for this to Work

1. **Image URLs must be public:** The URLs in `"path"` must be publicly accessible on the internet (not `localhost`). TikTok's servers need to be able to fetch them.
* *If you have local files:* You must first hit the Postiz upload endpoint (`POST /api/public/v1/upload-from-url` or `POST /api/public/v1/uploads`) to get a hosted URL, then use that URL in the syntax above.


2. **Integration ID:** You must first call `GET /api/public/v1/integrations` to find the specific UUID for your connected TikTok account.
3. **TikTok "Photo Mode" Limitations:**
* **Music:** Postiz API generally does not allow you to attach specific trending audio to carousels programmatically (TikTok API limitation). It will post with default/no sound or let TikTok assign one if the user settings allow.
* **Privacy:** If you are self-hosting and your app is "Unaudited," this payload will successfully upload the carousel, but it will be **locked to "Private"** visibility until you manually release it in the app.



### 4. Troubleshooting Common Errors

* **`file_format_check_failed`**: This often happens if you send images that are not strictly compliant. Ensure your images are **JPG** (PNGs often fail via API) and follow a **9:16 aspect ratio** (1080x1920).
* **Missing Title/Description**: There is a known bug in some versions of Postiz (issue #1059) where the title is stripped during "Upload" mode. If this happens, try adding `"settings": { "content_posting_method": "DIRECT_POST" }` inside the post object, though this requires your TikTok App to have the `video.publish` scope.

