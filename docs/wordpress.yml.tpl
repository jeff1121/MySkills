# WordPress + Redis + MariaDB 測試部署
# 使用方式: ./deploy.sh 或 envsubst < wordpress.yml.tpl | kubectl apply -f -
# 部署後透過 MetalLB 取得 External IP 存取 WordPress

---
apiVersion: v1
kind: Namespace
metadata:
  name: ${NAMESPACE}

---
apiVersion: v1
kind: Secret
metadata:
  name: mariadb-secret
  namespace: ${NAMESPACE}
type: Opaque
stringData:
  root-password: "${MARIADB_ROOT_PASSWORD}"
  database: "${MARIADB_DATABASE}"
  user: "${MARIADB_USER}"
  password: "${MARIADB_PASSWORD}"

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: mariadb-pvc
  namespace: ${NAMESPACE}
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: ${MARIADB_STORAGE_SIZE}

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mariadb
  namespace: ${NAMESPACE}
spec:
  replicas: 1
  selector:
    matchLabels:
      app: mariadb
  template:
    metadata:
      labels:
        app: mariadb
    spec:
      containers:
        - name: mariadb
          image: ${MARIADB_IMAGE}
          ports:
            - containerPort: 3306
          env:
            - name: MYSQL_ROOT_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: mariadb-secret
                  key: root-password
            - name: MYSQL_DATABASE
              valueFrom:
                secretKeyRef:
                  name: mariadb-secret
                  key: database
            - name: MYSQL_USER
              valueFrom:
                secretKeyRef:
                  name: mariadb-secret
                  key: user
            - name: MYSQL_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: mariadb-secret
                  key: password
          volumeMounts:
            - name: mariadb-storage
              mountPath: /var/lib/mysql
          resources:
            requests:
              memory: "${MARIADB_MEMORY_REQUEST}"
              cpu: "${MARIADB_CPU_REQUEST}"
            limits:
              memory: "${MARIADB_MEMORY_LIMIT}"
              cpu: "${MARIADB_CPU_LIMIT}"
      volumes:
        - name: mariadb-storage
          persistentVolumeClaim:
            claimName: mariadb-pvc

---
apiVersion: v1
kind: Service
metadata:
  name: mariadb
  namespace: ${NAMESPACE}
spec:
  selector:
    app: mariadb
  ports:
    - port: 3306
      targetPort: 3306
  type: ClusterIP

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: ${NAMESPACE}
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
        - name: redis
          image: ${REDIS_IMAGE}
          ports:
            - containerPort: 6379
          command: ["redis-server", "--appendonly", "yes"]
          resources:
            requests:
              memory: "${REDIS_MEMORY_REQUEST}"
              cpu: "${REDIS_CPU_REQUEST}"
            limits:
              memory: "${REDIS_MEMORY_LIMIT}"
              cpu: "${REDIS_CPU_LIMIT}"

---
apiVersion: v1
kind: Service
metadata:
  name: redis
  namespace: ${NAMESPACE}
spec:
  selector:
    app: redis
  ports:
    - port: 6379
      targetPort: 6379
  type: ClusterIP

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: wordpress-pvc
  namespace: ${NAMESPACE}
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: ${WORDPRESS_STORAGE_SIZE}

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: wordpress
  namespace: ${NAMESPACE}
spec:
  replicas: 1
  selector:
    matchLabels:
      app: wordpress
  template:
    metadata:
      labels:
        app: wordpress
    spec:
      containers:
        - name: wordpress
          image: ${WORDPRESS_IMAGE}
          ports:
            - containerPort: 80
          env:
            - name: WORDPRESS_DB_HOST
              value: "mariadb:3306"
            - name: WORDPRESS_DB_NAME
              valueFrom:
                secretKeyRef:
                  name: mariadb-secret
                  key: database
            - name: WORDPRESS_DB_USER
              valueFrom:
                secretKeyRef:
                  name: mariadb-secret
                  key: user
            - name: WORDPRESS_DB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: mariadb-secret
                  key: password
            - name: WP_REDIS_HOST
              value: "redis"
            - name: WP_REDIS_PORT
              value: "6379"
          volumeMounts:
            - name: wordpress-storage
              mountPath: /var/www/html
          resources:
            requests:
              memory: "${WORDPRESS_MEMORY_REQUEST}"
              cpu: "${WORDPRESS_CPU_REQUEST}"
            limits:
              memory: "${WORDPRESS_MEMORY_LIMIT}"
              cpu: "${WORDPRESS_CPU_LIMIT}"
      volumes:
        - name: wordpress-storage
          persistentVolumeClaim:
            claimName: wordpress-pvc

---
apiVersion: v1
kind: Service
metadata:
  name: wordpress
  namespace: ${NAMESPACE}
  annotations:
    metallb.universe.tf/address-pool: ${METALLB_ADDRESS_POOL}
spec:
  selector:
    app: wordpress
  ports:
    - port: 80
      targetPort: 80
  type: LoadBalancer
