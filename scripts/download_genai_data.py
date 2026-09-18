import os
from datasets import load_dataset
from PIL import Image

def main():
    print("Downloading synthetic GenAI images from Hugging Face...")
    
    # We will use 'saakshigupta/gradcam-fake-real-faces-xception' as a source of fake/real images
    # or another dataset. Let's try to load 'TheKernel01/140k-Real-and-Fake-Faces' in streaming mode.
    try:
        ds = load_dataset('TheKernel01/140k-Real-and-Fake-Faces', split='train', streaming=True)
        
        real_dir = "data/raw/real"
        fake_dir = "data/raw/fake"
        
        os.makedirs(real_dir, exist_ok=True)
        os.makedirs(fake_dir, exist_ok=True)
        
        real_count = 0
        fake_count = 0
        limit = 200
        
        for sample in ds:
            # The structure is usually an image and a label
            # Assuming 'image' and 'label' keys (0=Real, 1=Fake) or similar.
            img = sample['image']
            label = sample['label']
            
            if label == 0 and real_count < limit:
                img.save(os.path.join(real_dir, f"genai_real_{real_count}.jpg"))
                real_count += 1
            elif label == 1 and fake_count < limit:
                img.save(os.path.join(fake_dir, f"genai_fake_{fake_count}.jpg"))
                fake_count += 1
                
            if real_count >= limit and fake_count >= limit:
                break
                
        print(f"Successfully downloaded {real_count} real and {fake_count} synthetic fake images.")
    except Exception as e:
        print(f"Error loading datasets: {e}")

if __name__ == "__main__":
    main()
