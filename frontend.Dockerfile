# Step 1: Use an official node image as the base image
FROM node:16-alpine AS build

# Step 2: Set the working directory inside the container
WORKDIR /app

# Step 3: Copy the package.json and package-lock.json files to the container
COPY package*.json ./

# Step 4: Install dependencies
RUN npm install

# Step 5: Copy the rest of the application code to the container
COPY . .

# Step 6: Build the React application
RUN npm run build

# Step 7: Use a smaller, lightweight server to serve the built app
FROM nginx:alpine

# Step 8: Copy the built React app to the nginx server
COPY --from=build /app/build /usr/share/nginx/html

# Step 9: Expose the port on which the app will run
EXPOSE 80

# Step 10: Start the nginx server
CMD ["nginx", "-g", "daemon off;"]
