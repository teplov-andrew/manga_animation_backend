import asyncio
import fal_client

async def wan_generate(base64_image, prompt):
    
    # url = fal_client.upload_file(image_path)
    # print(url)
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


# if __name__ == "__main__":
#     asyncio.run(subscribe(image_path))