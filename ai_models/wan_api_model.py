import asyncio
import fal_client

async def wan_generate(base64_image, prompt):
    handler = await fal_client.submit_async(
        "fal-ai/wan-i2v",
        arguments={
            "prompt": prompt,
            "image_url": base64_image,
            "resolution": "480p"
        },
    )

    async for event in handler.iter_events(with_logs=True):
        print(event)

    result = await handler.get()

    print(result)
    return result