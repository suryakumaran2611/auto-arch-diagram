# Example: Using Custom Icons in Your Architecture Diagram

You can use custom icons in your diagrams by specifying the `Icon` tag in your Terraform or CloudFormation resources, or by providing an icon path as an input. The icon can be referenced in three ways:

1. **Built-in custom icon** (from `icons/custom/`):
   ```hcl
   resource "aws_lambda_function" "my_function" {
     # ...
     tags = {
       Name = "my-function"
       Icon = "custom://datapipeline"  # Will use icons/custom/datapipeline.png
     }
   }
   ```
2. **Absolute or relative path to a PNG icon**:
   ```hcl
   resource "aws_lambda_function" "my_function" {
     # ...
     tags = {
       Name = "my-function"
       Icon = "./my-icons/my-special-icon.png"  # Any accessible PNG file
     }
   }
   ```
3. **As a direct input to the diagram tool** (advanced):
   - If you are calling the diagram generator programmatically or via CLI, you can pass an icon path as an argument or in the resource dictionary under the `icon` key.

**Best Practice:**
- Place your custom icons in `icons/custom/` for easy reference and portability.
- Use the `custom://iconname` scheme for maintainability.
- CloudFormation resources automatically use appropriate service icons (S3, Lambda, CloudFront, etc.) based on resource types.

---

# Unit Test: Generate Images with Custom Icons

A test is provided in `tests/test_custom_icon_render.py` that generates diagrams using custom icons and saves the output images to `test-output/` for download and inspection.

---

# Downloading Generated Images

After running the test, you can download the generated images from the `test-output/` directory. These will include PNG and SVG diagrams with your custom icons rendered.

---

# Troubleshooting
- If a custom icon is not found, the tool will fall back to the default or provider icon.
- Ensure your icon filenames are lowercase and match the reference in the `Icon` tag.
- Supported format: PNG (recommended size: 64x64 or larger).
