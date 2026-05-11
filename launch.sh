#!/bin/bash
echo "Igniting OmniTwin Core..."

# Boot the backend neural cluster and UI server silently
docker-compose up -d

echo "Neural Cluster Online."
echo "Spawning Desktop Interface..."

# Launch the Electron wrapper
cd electron_app
npm start

# Once the Electron window is closed, autonomously teardown the background cluster
echo "Desktop Interface Closed. Terminating Neural Cluster..."
cd ..
docker-compose down
echo "OmniTwin Shutdown Complete."
