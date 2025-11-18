FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS base
WORKDIR /app
EXPOSE 5007

FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src

COPY ["src/Tinisoft.Shipping.API/Tinisoft.Shipping.API.csproj", "src/Tinisoft.Shipping.API/"]
COPY ["src/Tinisoft.Application/Tinisoft.Application.csproj", "src/Tinisoft.Application/"]
COPY ["src/Tinisoft.Domain/Tinisoft.Domain.csproj", "src/Tinisoft.Domain/"]
COPY ["src/Tinisoft.Infrastructure/Tinisoft.Infrastructure.csproj", "src/Tinisoft.Infrastructure/"]
COPY ["src/Tinisoft.Shared/Tinisoft.Shared.csproj", "src/Tinisoft.Shared/"]

RUN dotnet restore "src/Tinisoft.Shipping.API/Tinisoft.Shipping.API.csproj"
COPY . .
WORKDIR "/src/src/Tinisoft.Shipping.API"
RUN dotnet build "Tinisoft.Shipping.API.csproj" -c Release -o /app/build

FROM build AS publish
RUN dotnet publish "Tinisoft.Shipping.API.csproj" -c Release -o /app/publish /p:UseAppHost=false

FROM base AS final
WORKDIR /app
COPY --from=publish /app/publish .
ENTRYPOINT ["dotnet", "Tinisoft.Shipping.API.dll"]

