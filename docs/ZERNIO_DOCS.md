# TikTok API

> Schedule and automate TikTok posts with Zernio API - Videos, photo carousels, privacy settings, and AI disclosure

Source: Zernio API Documentation (https://docs.zernio.com)
API Base URL: https://zernio.com/api/v1

---

# TikTok API

Schedule and automate TikTok posts with Zernio API - Videos, photo carousels, privacy settings, and AI disclosure

import { Tab, Tabs } from 'fumadocs-ui/components/tabs';
import { Callout } from 'fumadocs-ui/components/callout';

## Quick Reference

| Property | Value |
|----------|-------|
| Character limit | 2,200 (video caption), 4,000 (photo desc) |
| Photo title | 90 chars (auto-truncated, hashtags stripped) |
| Photos per post | 35 (carousel) |
| Videos per post | 1 |
| Photo formats | JPEG, PNG, WebP |
| Photo max size | 20 MB |
| Video formats | MP4, MOV, WebM |
| Video max size | 4 GB |
| Video duration | 3 sec - 10 min |
| Post types | Video, Photo Carousel |
| Scheduling | Yes |
| Inbox (Comments) | No |
| Inbox (DMs) | No |
| Analytics | Limited |

## Before You Start

<Callout type="warn">
TikTok has a strict daily posting limit for posts created via third-party APIs. This limit is separate from the native app and is account-specific. When you hit it, the only options are to wait or post directly in TikTok. Also: the privacy levels available via API depend on each creator's TikTok account settings. You must fetch the creator's allowed levels and only use those, or the post will fail.

Additional requirements:
- Each creator has account-specific privacy level options
- Content moderation is more aggressive via API than native app
- All posts require consent flags (legal requirement from TikTok)
- No text-only posts (media required)
</Callout>

## Quick Start

Post a video to TikTok in under 60 seconds:

<Tabs items={['Node.js', 'Python', 'curl']}>
<Tab value="Node.js">
```typescript
const { post } = await zernio.posts.createPost({
  content: 'Check out this amazing sunset! #sunset #nature',
  mediaItems: [
    { type: 'video', url: 'https://cdn.example.com/sunset-video.mp4' }
  ],
  platforms: [
    { platform: 'tiktok', accountId: 'YOUR_ACCOUNT_ID' }
  ],
  tiktokSettings: {
    privacy_level: 'PUBLIC_TO_EVERYONE',
    allow_comment: true,
    allow_duet: true,
    allow_stitch: true,
    content_preview_confirmed: true,
    express_consent_given: true
  },
  publishNow: true
});
console.log('Posted to TikTok!', post._id);
```
</Tab>
<Tab value="Python">
```python
result = client.posts.create_post(
    content="Check out this amazing sunset! #sunset #nature",
    media_items=[
        {"type": "video", "url": "https://cdn.example.com/sunset-video.mp4"}
    ],
    platforms=[
        {"platform": "tiktok", "accountId": "YOUR_ACCOUNT_ID"}
    ],
    tiktok_settings={
        "privacy_level": "PUBLIC_TO_EVERYONE",
        "allow_comment": True,
        "allow_duet": True,
        "allow_stitch": True,
        "content_preview_confirmed": True,
        "express_consent_given": True
    },
    publish_now=True
)
post = result.post
print(f"Posted to TikTok! {post['_id']}")
```
</Tab>
<Tab value="curl">
```bash
curl -X POST https://zernio.com/api/v1/posts \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Check out this amazing sunset! #sunset #nature",
    "mediaItems": [
      {"type": "video", "url": "https://cdn.example.com/sunset-video.mp4"}
    ],
    "platforms": [
      {"platform": "tiktok", "accountId": "YOUR_ACCOUNT_ID"}
    ],
    "tiktokSettings": {
      "privacy_level": "PUBLIC_TO_EVERYONE",
      "allow_comment": true,
      "allow_duet": true,
      "allow_stitch": true,
      "content_preview_confirmed": true,
      "express_consent_given": true
    },
    "publishNow": true
  }'
```
</Tab>
</Tabs>

## Content Types

### Video Post

A single video post. Videos must be between 3 seconds and 10 minutes long. Vertical 9:16 aspect ratio is the only format that works well on TikTok.

<Tabs items={['Node.js', 'Python', 'curl']}>
<Tab value="Node.js">
```typescript
const { post } = await zernio.posts.createPost({
  content: 'New cooking tutorial #recipe #foodtok',
  mediaItems: [
    { type: 'video', url: 'https://cdn.example.com/cooking-tutorial.mp4' }
  ],
  platforms: [
    { platform: 'tiktok', accountId: 'YOUR_ACCOUNT_ID' }
  ],
  tiktokSettings: {
    privacy_level: 'PUBLIC_TO_EVERYONE',
    allow_comment: true,
    allow_duet: true,
    allow_stitch: true,
    video_cover_timestamp_ms: 3000,
    content_preview_confirmed: true,
    express_consent_given: true
  },
  publishNow: true
});
console.log('Video posted!', post._id);
```
</Tab>
<Tab value="Python">
```python
result = client.posts.create_post(
    content="New cooking tutorial #recipe #foodtok",
    media_items=[
        {"type": "video", "url": "https://cdn.example.com/cooking-tutorial.mp4"}
    ],
    platforms=[
        {"platform": "tiktok", "accountId": "YOUR_ACCOUNT_ID"}
    ],
    tiktok_settings={
        "privacy_level": "PUBLIC_TO_EVERYONE",
        "allow_comment": True,
        "allow_duet": True,
        "allow_stitch": True,
        "video_cover_timestamp_ms": 3000,
        "content_preview_confirmed": True,
        "express_consent_given": True
    },
    publish_now=True
)
post = result.post
print(f"Video posted! {post['_id']}")
```
</Tab>
<Tab value="curl">
```bash
curl -X POST https://zernio.com/api/v1/posts \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "New cooking tutorial #recipe #foodtok",
    "mediaItems": [
      {"type": "video", "url": "https://cdn.example.com/cooking-tutorial.mp4"}
    ],
    "platforms": [
      {"platform": "tiktok", "accountId": "YOUR_ACCOUNT_ID"}
    ],
    "tiktokSettings": {
      "privacy_level": "PUBLIC_TO_EVERYONE",
      "allow_comment": true,
      "allow_duet": true,
      "allow_stitch": true,
      "video_cover_timestamp_ms": 3000,
      "content_preview_confirmed": true,
      "express_consent_given": true
    },
    "publishNow": true
  }'
```
</Tab>
</Tabs>

### Custom Video Thumbnail

For video posts, you can set a custom cover image using `video_cover_image_url`. When provided, it overrides `video_cover_timestamp_ms`.

<Tabs items={['Node.js', 'Python', 'curl']}>
<Tab value="Node.js">
```typescript
const { post } = await zernio.posts.createPost({
  content: 'New product teaser #launch',
  mediaItems: [
    { type: 'video', url: 'https://cdn.example.com/teaser.mp4' }
  ],
  platforms: [
    { platform: 'tiktok', accountId: 'YOUR_ACCOUNT_ID' }
  ],
  tiktokSettings: {
    privacy_level: 'PUBLIC_TO_EVERYONE',
    allow_comment: true,
    allow_duet: true,
    allow_stitch: true,
    video_cover_image_url: 'https://cdn.example.com/teaser-cover.jpg',
    content_preview_confirmed: true,
    express_consent_given: true
  },
  publishNow: true
});
console.log('Video posted!', post._id);
```
</Tab>
<Tab value="Python">
```python
result = client.posts.create_post(
    content="New product teaser #launch",
    media_items=[
        {"type": "video", "url": "https://cdn.example.com/teaser.mp4"}
    ],
    platforms=[
        {"platform": "tiktok", "accountId": "YOUR_ACCOUNT_ID"}
    ],
    tiktok_settings={
        "privacy_level": "PUBLIC_TO_EVERYONE",
        "allow_comment": True,
        "allow_duet": True,
        "allow_stitch": True,
        "video_cover_image_url": "https://cdn.example.com/teaser-cover.jpg",
        "content_preview_confirmed": True,
        "express_consent_given": True
    },
    publish_now=True
)
post = result.post
print(f"Video posted! {post['_id']}")
```
</Tab>
<Tab value="curl">
```bash
curl -X POST https://zernio.com/api/v1/posts \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "New product teaser #launch",
    "mediaItems": [
      {"type": "video", "url": "https://cdn.example.com/teaser.mp4"}
    ],
    "platforms": [
      {"platform": "tiktok", "accountId": "YOUR_ACCOUNT_ID"}
    ],
    "tiktokSettings": {
      "privacy_level": "PUBLIC_TO_EVERYONE",
      "allow_comment": true,
      "allow_duet": true,
      "allow_stitch": true,
      "video_cover_image_url": "https://cdn.example.com/teaser-cover.jpg",
      "content_preview_confirmed": true,
      "express_consent_given": true
    },
    "publishNow": true
  }'
```
</Tab>
</Tabs>

### Photo Carousel

Up to 35 images in a single post. Photos are auto-resized to 1080x1920. The `content` field becomes the photo title (90 chars max, hashtags and URLs are auto-stripped). Use the `description` field inside `tiktokSettings` for a full caption up to 4,000 characters.

<Tabs items={['Node.js', 'Python', 'curl']}>
<Tab value="Node.js">
```typescript
const { post } = await zernio.posts.createPost({
  content: 'My travel highlights',
  mediaItems: [
    { type: 'image', url: 'https://cdn.example.com/photo1.jpg' },
    { type: 'image', url: 'https://cdn.example.com/photo2.jpg' },
    { type: 'image', url: 'https://cdn.example.com/photo3.jpg' }
  ],
  platforms: [
    { platform: 'tiktok', accountId: 'YOUR_ACCOUNT_ID' }
  ],
  tiktokSettings: {
    privacy_level: 'PUBLIC_TO_EVERYONE',
    allow_comment: true,
    media_type: 'photo',
    photo_cover_index: 0,
    description: 'Full trip recap from our weekend adventure across the coast. These are the best moments we captured along the way! #travel #roadtrip #adventure',
    auto_add_music: true,
    content_preview_confirmed: true,
    express_consent_given: true
  },
  publishNow: true
});
console.log('Photo carousel posted!', post._id);
```
</Tab>
<Tab value="Python">
```python
result = client.posts.create_post(
    content="My travel highlights",
    media_items=[
        {"type": "image", "url": "https://cdn.example.com/photo1.jpg"},
        {"type": "image", "url": "https://cdn.example.com/photo2.jpg"},
        {"type": "image", "url": "https://cdn.example.com/photo3.jpg"}
    ],
    platforms=[
        {"platform": "tiktok", "accountId": "YOUR_ACCOUNT_ID"}
    ],
    tiktok_settings={
        "privacy_level": "PUBLIC_TO_EVERYONE",
        "allow_comment": True,
        "media_type": "photo",
        "photo_cover_index": 0,
        "description": "Full trip recap from our weekend adventure across the coast. These are the best moments we captured along the way! #travel #roadtrip #adventure",
        "auto_add_music": True,
        "content_preview_confirmed": True,
        "express_consent_given": True
    },
    publish_now=True
)
post = result.post
print(f"Photo carousel posted! {post['_id']}")
```
</Tab>
<Tab value="curl">
```bash
curl -X POST https://zernio.com/api/v1/posts \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "My travel highlights",
    "mediaItems": [
      {"type": "image", "url": "https://cdn.example.com/photo1.jpg"},
      {"type": "image", "url": "https://cdn.example.com/photo2.jpg"},
      {"type": "image", "url": "https://cdn.example.com/photo3.jpg"}
    ],
    "platforms": [
      {"platform": "tiktok", "accountId": "YOUR_ACCOUNT_ID"}
    ],
    "tiktokSettings": {
      "privacy_level": "PUBLIC_TO_EVERYONE",
      "allow_comment": true,
      "media_type": "photo",
      "photo_cover_index": 0,
      "description": "Full trip recap from our weekend adventure across the coast. These are the best moments we captured along the way! #travel #roadtrip #adventure",
      "auto_add_music": true,
      "content_preview_confirmed": true,
      "express_consent_given": true
    },
    "publishNow": true
  }'
```
</Tab>
</Tabs>

## Media Requirements

### Images

| Property | Requirement |
|----------|-------------|
| **Max photos** | 35 per carousel |
| **Formats** | JPEG, PNG, WebP |
| **Max file size** | 20 MB per image |
| **Aspect ratio** | 9:16 recommended |
| **Resolution** | Auto-resized to 1080 x 1920 px |

### Videos

| Property | Requirement |
|----------|-------------|
| **Max videos** | 1 per post |
| **Formats** | MP4, MOV, WebM |
| **Max file size** | 4 GB |
| **Max duration** | 10 minutes |
| **Min duration** | 3 seconds |
| **Aspect ratio** | 9:16 vertical (only format that works well) |
| **Resolution** | 1080 x 1920 px recommended |
| **Codec** | H.264 |
| **Frame rate** | 30 fps recommended |

You cannot mix photos and videos in the same post. Use either all photos (carousel) or one video.

## Platform-Specific Fields

TikTok settings go in `tiktokSettings` at the **top level** of the request body, not inside `platformSpecificData`. This is a special case unique to TikTok.

## TikTok Creator Info

Use this endpoint to fetch the creator's allowed `privacyLevels`, current `postingLimits` (including interaction defaults), and available `commercialContentTypes` before creating a post.

> **Note:** This endpoint only works for TikTok accounts. If you pass a non-TikTok `accountId`, you'll get a 400 error.

<Tabs items={['curl', 'JavaScript', 'Python']}>
<Tab value="curl">
```bash
curl "https://zernio.com/api/v1/accounts/YOUR_ACCOUNT_ID/tiktok/creator-info?mediaType=video" \
  -H "Authorization: Bearer YOUR_API_KEY"
```
</Tab>
<Tab value="JavaScript">
```typescript
const info = await zernio.accounts.getTikTokCreatorInfo({
  accountId: 'YOUR_ACCOUNT_ID',
  mediaType: 'video'
});

console.log(info.creator);
console.log(info.privacyLevels);
console.log(info.postingLimits);
console.log(info.commercialContentTypes);
```
</Tab>
<Tab value="Python">
```python
info = client.accounts.get_tik_tok_creator_info(
    account_id="YOUR_ACCOUNT_ID",
    media_type="video"
)

print(info["creator"])
print(info["privacyLevels"])
print(info["postingLimits"])
print(info["commercialContentTypes"])
```
</Tab>
</Tabs>

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `privacy_level` | string | Yes | Must match creator's allowed values. Options: `PUBLIC_TO_EVERYONE`, `MUTUAL_FOLLOW_FRIENDS`, `FOLLOWER_OF_CREATOR`, `SELF_ONLY` |
| `allow_comment` | boolean | Yes | Enable or disable comments on the post |
| `allow_duet` | boolean | Yes (videos) | Enable or disable duets. Only applies to video posts. |
| `allow_stitch` | boolean | Yes (videos) | Enable or disable stitches. Only applies to video posts. |
| `content_preview_confirmed` | boolean | Yes | Must be `true`. Legal requirement from TikTok. |
| `express_consent_given` | boolean | Yes | Must be `true`. Legal requirement from TikTok. |
| `video_cover_timestamp_ms` | number | No | Thumbnail frame position in milliseconds. Default: `1000`. Ignored when `video_cover_image_url` is provided. |
| `video_cover_image_url` | string | No | Custom thumbnail image URL (JPG, PNG, or WebP, max 20MB). Overrides `video_cover_timestamp_ms`. |
| `media_type` | `"photo"` | No | Set to `"photo"` for photo carousels. |
| `photo_cover_index` | number | No | Which image to use as cover (0-indexed). |
| `description` | string | No | Long-form caption for photo carousels, up to 4,000 characters. |
| `auto_add_music` | boolean | No | Let TikTok add recommended music. Photo carousels only. |
| `video_made_with_ai` | boolean | No | AI-generated content disclosure flag. |
| `draft` | boolean | No | Send to Creator Inbox for review instead of publishing. |
| `commercialContentType` | string | No | `"none"`, `"brand_organic"`, or `"brand_content"`. |

### Photo Carousel Caption Behavior

The `content` field and `description` field serve different purposes for photo carousels:

- **`content`** (top-level) -- becomes the photo **title**. Limited to 90 characters. Hashtags and URLs are auto-stripped.
- **`description`** (inside `tiktokSettings`) -- becomes the full **caption** shown below the carousel. Up to 4,000 characters.

## Media URL Requirements

<Callout type="error">
**These do not work as media URLs:**
- **Google Drive** -- returns an HTML download page, not the file
- **Dropbox** -- returns an HTML preview page
- **OneDrive / SharePoint** -- returns HTML
- **iCloud** -- returns HTML

Test your URL in an incognito browser window. If you see a webpage instead of the raw video or image, it will not work.
</Callout>

Media URLs must be:
- Publicly accessible (no authentication required)
- Returning actual media bytes with the correct `Content-Type` header
- Not behind redirects that resolve to HTML pages
- Hosted on a fast, reliable CDN

Large videos are auto-chunked during upload (5-64 MB per chunk). Photos are auto-resized to 1080x1920.

## Analytics

> **Included** — Analytics is bundled with every paid account on the [Usage plan](/pricing).

Available metrics via the [Analytics API](/analytics/get-analytics):

| Metric | Available |
|--------|-----------|
| Likes | ✅ |
| Comments | ✅ |
| Shares | ✅ |
| Views | ✅ |

TikTok also provides a dedicated [Account Insights API](/analytics/get-tiktok-account-insights) for account-level counters (follower_count, following_count, likes_count, video_count) plus Zernio-synthesized followers_gained and followers_lost deltas. Live values come from TikTok's user.info.stats scope; historical time series is joined from Zernio's daily snapshotter.

Deep metrics from TikTok Studio (profile views, account-level impressions and reach, per-video watch time and average watch time, full-watched rate, impression sources like FYP / Following / Hashtag / Search) are not available on any TikTok public API. TikTok's Research API does not expose these either and is restricted to non-commercial academic use per TikTok's eligibility policy. There is no public API workaround.

<Tabs items={['Node.js', 'Python', 'curl']}>
<Tab value="Node.js">
```typescript
const analytics = await zernio.analytics.getAnalytics({
  platform: 'tiktok',
  fromDate: '2024-01-01',
  toDate: '2024-01-31'
});
console.log(analytics.posts);
```
</Tab>
<Tab value="Python">
```python
analytics = client.analytics.get_analytics(
    platform="tiktok",
    from_date="2024-01-01",
    to_date="2024-01-31"
)
print(analytics["posts"])
```
</Tab>
<Tab value="curl">
```bash
curl "https://zernio.com/api/v1/analytics?platform=tiktok&fromDate=2024-01-01&toDate=2024-01-31" \
  -H "Authorization: Bearer YOUR_API_KEY"
```
</Tab>
</Tabs>

## What You Can't Do

These features are not available through TikTok's API:

- Use TikTok's sound/music library (except `auto_add_music` for photo carousels)
- Create duets or stitches
- Go Live
- Add effects or filters
- Edit posts after publishing
- View For You Page analytics
- Create playlists
- Read or write comments
- Send or read DMs
- Create text-only posts (media required)

## Common Errors

TikTok has a **13.1% failure rate** across Zernio's platform (30,746 failures out of 235,045 attempts). Here are the most frequent errors and how to fix them:

| Error | Meaning | Fix |
|-------|---------|-----|
| "You have created too many posts in the last 24 hours via the API." | TikTok's daily API posting limit hit | Wait until limit resets (24h rolling) or post directly in TikTok app. |
| "Publishing failed during platform API call (timeout waiting for platform response)" | TikTok's servers took too long to process | For large videos this can be normal. Check post status after a few minutes. |
| "Selected privacy level 'X' is not available for this creator. Available options: ..." | Privacy level does not match creator's account settings | Fetch creator info to get allowed privacy levels and use one of those. |
| "TikTok flagged this post as potentially risky (spam_risk)" | Content moderation flagged the post | Review content. TikTok's API moderation is stricter than the native app. |
| "Duplicate content detected." | Same content was already posted recently | Modify the caption or media before retrying. |
| "TikTok video upload failed: Your video URL returned an error (download failed)" | TikTok could not download the video from the URL | Ensure the URL is a direct download link, not a cloud storage sharing page. |
| "Missing required TikTok permissions. Please reconnect with all required scopes." | OAuth token is missing required scopes | Reconnect the TikTok account with all required permissions. |

## Inbox

> **Included** — Inbox (DMs, comments, reviews) is bundled with every paid account on the [Usage plan](/pricing).

TikTok has no inbox support.

### Comments

| Feature | Supported |
|---------|-----------|
| List comments on posts | ❌ |
| Post new comment | ❌ |
| Reply to comments | ❌ |
| Delete comments | ❌ |

### Limitations

- **No comments support** - Zernio does not currently support TikTok comments
- **No DMs** - Zernio does not currently support TikTok DMs

## Related Endpoints

- [Connect TikTok Account](/guides/connecting-accounts) - OAuth flow
- [Create Post](/posts/create-post) - Post creation and scheduling
- [Upload Media](/guides/media-uploads) - Image and video uploads
- [Analytics](/analytics/get-analytics) - Performance metrics
- [Comments](/comments/list-inbox-comments) - Comments API Reference