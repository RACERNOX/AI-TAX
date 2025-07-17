# 🚨 Render Deployment Troubleshooting Guide

## Primary Issues Identified & Solutions

### 1. **API Quota Exceeded (Critical)**
**Problem**: Your Google Gemini API has exceeded the free tier quota (50 requests/day)
**Solution**: 
- Get a new API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
- OR upgrade to a paid plan for higher limits
- OR wait 24 hours for quota reset

### 2. **Port Configuration Fixed**
**Problem**: Mismatch between render.yaml and app.py port settings
**Solution**: ✅ Fixed - Now both use port 10000 (Render's default)

### 3. **Dependency Conflicts**
**Problem**: Complex build command and dependency issues
**Solution**: ✅ Fixed - Simplified build process and created `requirements-render.txt`

### 4. **System Dependencies**
**Problem**: Heavy system dependencies causing build timeouts
**Solution**: ✅ Fixed - Removed unnecessary system package installations

---

## Deployment Steps (Updated)

### Step 1: Update Your Repository
```bash
# Push these fixes to your GitHub repository
git add .
git commit -m "Fix Render deployment issues - simplified dependencies and port config"
git push origin main
```

### Step 2: Deploy on Render
1. Go to [render.com](https://render.com)
2. Create new Web Service
3. Connect your GitHub repository
4. Render will auto-detect settings from `render.yaml`
5. **IMPORTANT**: Set environment variables:
   - `GEMINI_API_KEY`: Your new API key
   - `PORT`: 10000 (should be auto-set)

### Step 3: Monitor Deployment
Check build logs for these success indicators:
```
✅ Dependencies installed successfully
✅ Gemini API connection verified
✅ Starting GreenGrowth CPAs AI Tax Agent on 0.0.0.0:10000
```

---

## Common Deployment Errors & Solutions

### Error: "Build failed - dependency conflict"
**Cause**: Requirements.txt has conflicting versions
**Solution**: Use `requirements-render.txt` (already updated in render.yaml)

### Error: "Port binding failed"
**Cause**: Port configuration mismatch
**Solution**: ✅ Fixed - Port now correctly set to 10000

### Error: "API connection failed"
**Cause**: Missing or invalid GEMINI_API_KEY
**Solution**: 
1. Generate new API key
2. Add to Render environment variables
3. Redeploy

### Error: "Build timeout"
**Cause**: Heavy system dependencies
**Solution**: ✅ Fixed - Removed unnecessary apt-get installs

### Error: "Memory limit exceeded"
**Cause**: PDF processing using too much memory
**Solution**: App already uses memory-only processing - should be fine

---

## Health Check After Deployment

1. **Test Health Endpoint**:
   ```
   GET https://your-app-name.onrender.com/health
   ```
   Should return:
   ```json
   {
     "status": "healthy",
     "services": {
       "gemini_api": "connected",
       "file_system": "accessible",
       "processing_engines": "ready"
     }
   }
   ```

2. **Test File Upload**:
   - Visit your app URL
   - Upload a small PDF
   - Check for successful processing

---

## If Deployment Still Fails

### Check Build Logs
Look for specific errors in Render dashboard → Build logs

### Common Issues:
1. **API Key Issues**: Generate fresh API key
2. **Python Version**: Ensure Python 3.9.18 (set in runtime.txt)
3. **File Permissions**: App uses /tmp directories (should work)
4. **Memory Issues**: Consider upgrading to paid plan if needed

### Emergency Fallback
If all else fails, here's a minimal deployment approach:

1. **Remove unnecessary features temporarily**:
   - Comment out complex PDF processing
   - Use basic text processing only

2. **Minimal requirements.txt**:
   ```
   Flask==3.0.0
   google-generativeai==0.3.2
   ```

3. **Simple render.yaml**:
   ```yaml
   services:
     - type: web
       name: taxagent-pro
       env: python
       buildCommand: pip install -r requirements.txt
       startCommand: python app.py
   ```

---

## Final Deployment Checklist

- [ ] New GEMINI_API_KEY obtained and set
- [ ] Repository updated with fixes
- [ ] render.yaml using requirements-render.txt
- [ ] App.py port set to 10000
- [ ] Build logs show no errors
- [ ] Health endpoint returns "healthy"
- [ ] Basic file upload works

---

## Support Resources

- **Render Docs**: https://render.com/docs
- **Google AI Studio**: https://makersuite.google.com/app/apikey
- **App Health Check**: https://your-app-name.onrender.com/health

**Your app should now deploy successfully with these fixes!**
