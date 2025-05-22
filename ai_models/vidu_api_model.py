import asyncio
import fal_client
import json
 
async def vidu_generate(base64_image, prompt):
    # base64 = path2base64URI(image_path)
    # url = fal_client.upload_file(image_path)
    handler = await fal_client.submit_async(
        "fal-ai/vidu/q1/image-to-video",
        arguments={
            "prompt": prompt,
            "image_url": base64_image
        },
    )

    async for event in handler.iter_events(with_logs=True):
        print(event)

    result = await handler.get()

    print(result)
    return result





# if __name__ == "__main__":
#     asyncio.run(subscribe("/Users/andrew/Documents/images/img2.png", "a man is talking"))