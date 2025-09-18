# CPC New Haven - Deployment Guide

## Render.com Deployment

### Prerequisites
- GitHub repository with your code
- Render.com account

### Deployment Steps

1. **Connect Repository**
   - Go to [Render.com](https://render.com)
   - Sign up/Login with your GitHub account
   - Click "New +" → "Web Service"
   - Connect your GitHub repository

2. **Configure Service**
   - **Name**: `cpc-new-haven`
   - **Environment**: `Python 3`
   - **Build Command**: 
     ```bash
     pip install -r requirements.txt
     python migrate_data.py
     ```
   - **Start Command**: 
     ```bash
     gunicorn app:app
     ```

3. **Environment Variables**
   Set these in the Render dashboard:
   - `FLASK_ENV`: `production`
   - `SECRET_KEY`: Generate a secure secret key
   - `DATABASE_URL`: Will be provided by Render's PostgreSQL service

4. **Database Setup**
   - Go to "New +" → "PostgreSQL"
   - Name: `cpc-database`
   - Plan: Free tier
   - Connect the database to your web service

5. **Deploy**
   - Click "Create Web Service"
   - Render will automatically build and deploy your application

### Alternative: Using render.yaml

If you prefer to use the `render.yaml` file:

1. Push your code to GitHub
2. In Render dashboard, select "New +" → "Blueprint"
3. Connect your repository
4. Render will automatically detect and use the `render.yaml` configuration

## Manual Deployment Commands

### Start Command for Render.com
```bash
gunicorn app:app
```

### Build Command for Render.com
```bash
pip install -r requirements.txt
python migrate_data.py
```

## Environment Variables

### Required
- `FLASK_ENV`: Set to `production` for production deployment
- `SECRET_KEY`: A secure secret key for Flask sessions
- `DATABASE_URL`: PostgreSQL connection string (provided by Render)

### Optional
- `PORT`: Port number (Render will set this automatically)
- `DEBUG`: Set to `False` in production

## Database Migration

The application will automatically:
1. Create database tables on first run
2. Run data migration to populate sample data
3. Set up admin interface

## Monitoring and Logs

- View application logs in the Render dashboard
- Monitor performance and errors
- Set up alerts for downtime

## Custom Domain

1. In Render dashboard, go to your service settings
2. Add your custom domain
3. Update DNS records as instructed
4. SSL certificate will be automatically provisioned

## Troubleshooting

### Common Issues

1. **Build Failures**
   - Check that all dependencies are in `requirements.txt`
   - Ensure Python version compatibility
   - Check build logs for specific errors

2. **Database Connection Issues**
   - Verify `DATABASE_URL` is correctly set
   - Ensure PostgreSQL service is running
   - Check database credentials

3. **Application Crashes**
   - Check application logs
   - Verify all environment variables are set
   - Ensure database tables are created

### Debug Mode

To enable debug mode temporarily:
1. Set `FLASK_ENV=development` in environment variables
2. Redeploy the service
3. Check logs for detailed error information

## Performance Optimization

### Production Settings
- Use Gunicorn with multiple workers
- Enable database connection pooling
- Set up CDN for static assets
- Configure caching headers

### Scaling
- Upgrade to paid plans for better performance
- Add more workers for higher traffic
- Use Redis for session storage
- Implement database read replicas

## Security Considerations

1. **Environment Variables**
   - Never commit secrets to version control
   - Use strong, unique secret keys
   - Rotate keys regularly

2. **Database Security**
   - Use strong database passwords
   - Enable SSL connections
   - Regular backups

3. **Application Security**
   - Keep dependencies updated
   - Use HTTPS in production
   - Implement rate limiting
   - Regular security audits

## Backup Strategy

1. **Database Backups**
   - Render provides automatic PostgreSQL backups
   - Download backups regularly
   - Test restore procedures

2. **Code Backups**
   - Use Git for version control
   - Tag stable releases
   - Keep multiple repository copies

## Monitoring

### Health Checks
- Application health endpoint: `/`
- Database connectivity checks
- Admin interface accessibility: `/admin`

### Metrics to Monitor
- Response times
- Error rates
- Database performance
- Memory usage
- CPU utilization

## Support

For deployment issues:
1. Check Render documentation
2. Review application logs
3. Test locally first
4. Contact Render support if needed

## Cost Optimization

### Free Tier Limits
- 750 hours per month
- 512MB RAM
- 1GB disk space
- Sleeps after 15 minutes of inactivity

### Upgrade Considerations
- Paid plans start at $7/month
- No sleep mode
- More resources
- Better performance
